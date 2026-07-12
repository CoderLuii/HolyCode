#!/bin/bash
set -e

# ==============================================================================
# HolyCode - Container Entrypoint
# Handles: UID/GID remapping, directory pre-creation, first-boot bootstrap,
#          s6-overlay handoff
# ==============================================================================

OC_USER="opencode"
OC_HOME="/home/opencode"
WORKSPACE_DIR="/workspace"
CLAUDE_AUTH_PLUGIN_NAME="opencode-claude-auth"
CLAUDE_AUTH_PLUGIN_VERSION="2.0.0"
OH_MY_OPENAGENT_PLUGIN_NAME="oh-my-openagent"
OH_MY_OPENAGENT_PLUGIN_VERSION="4.17.0"

sync_shipped_skills() {
    local source_skills_dir="/usr/local/share/holycode/skills"
    local target_skills_dir="$OC_HOME/.config/opencode/skills"
    local oh_my_openagent_skill="oh-my-openagent-setup"

    [ -d "$source_skills_dir" ] || return 0

    mkdir -p "$target_skills_dir"
    chown "$PUID:$PGID" "$target_skills_dir"

    local oh_skill_target="$target_skills_dir/$oh_my_openagent_skill"
    local oh_skill_marker="$oh_skill_target/.holycode-managed"

    if [ "${ENABLE_OH_MY_OPENAGENT}" = "true" ]; then
        if [ ! -e "$oh_skill_target" ]; then
            if [ -d "$source_skills_dir/$oh_my_openagent_skill" ]; then
                cp -R "$source_skills_dir/$oh_my_openagent_skill" "$oh_skill_target"
                touch "$oh_skill_marker"
                chown -R "$PUID:$PGID" "$oh_skill_target"
                echo "[entrypoint] Installed built-in skill '$oh_my_openagent_skill'"
            fi
        elif [ ! -f "$oh_skill_marker" ]; then
            echo "[entrypoint] Skill '$oh_my_openagent_skill' exists (not HolyCode-managed), skipping"
        fi
    else
        if [ -f "$oh_skill_marker" ]; then
            rm -rf "$oh_skill_target"
            echo "[entrypoint] Removed HolyCode-managed skill '$oh_my_openagent_skill'"
        fi
    fi

    find "$source_skills_dir" -mindepth 1 -maxdepth 1 -type d | while read -r skill_dir; do
        local skill_name target_dir
        skill_name=$(basename "$skill_dir")
        target_dir="$target_skills_dir/$skill_name"

        [ "$skill_name" = "$oh_my_openagent_skill" ] && continue

        if [ -e "$target_dir" ]; then
            continue
        fi

        cp -R "$skill_dir" "$target_dir"
        chown -R "$PUID:$PGID" "$target_dir"
        echo "[entrypoint] Installed built-in skill '$skill_name'"
    done
}

plugin_config_spec() {
    local config_file="$1"
    local plugin_name="$2"

    [ -f "$config_file" ] || return 1
    python3 - "$config_file" "$plugin_name" 2>/dev/null <<'PY'
import json
import sys

with open(sys.argv[1], 'r', encoding='utf-8') as f:
    config = json.load(f)

plugin_name = sys.argv[2]
plugins = config.get('plugin', []) if isinstance(config, dict) else []
for plugin in plugins:
    if isinstance(plugin, str) and (plugin == plugin_name or plugin.startswith(f'{plugin_name}@')):
        print(plugin)
        sys.exit(0)
sys.exit(1)
PY
}

remove_plugin_config() {
    local config_file="$1"
    local plugin_name="$2"

    [ -f "$config_file" ] || return 1
    runuser -u "$OC_USER" -- python3 - "$config_file" "$plugin_name" 2>/dev/null <<'PY'
import json
import sys

config_file = sys.argv[1]
plugin_name = sys.argv[2]

with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

plugins = config.get('plugin', []) if isinstance(config, dict) else []
if not isinstance(plugins, list):
    sys.exit(1)

filtered = [
    plugin
    for plugin in plugins
    if not (
        isinstance(plugin, str)
        and (plugin == plugin_name or plugin.startswith(f'{plugin_name}@'))
    )
]
if filtered == plugins:
    sys.exit(1)

if filtered:
    config['plugin'] = filtered
else:
    config.pop('plugin', None)

with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2)
    f.write('\n')
PY
}

plugin_installed_version() {
    local plugin_name="$1"
    local plugin_spec="${2:-}"
    local package_json

    if [ -z "$plugin_spec" ]; then
        plugin_spec=$(plugin_config_spec "$CONFIG_FILE" "$plugin_name" || true)
    fi
    [ -n "$plugin_spec" ] || return 1

    if [ "$plugin_spec" = "$plugin_name" ]; then
        plugin_spec="${plugin_name}@latest"
    fi
    package_json="$OC_HOME/.cache/opencode/packages/$plugin_spec/node_modules/$plugin_name/package.json"

    [ -f "$package_json" ] || return 1
    python3 - "$package_json" 2>/dev/null <<'PY'
import json
import sys

with open(sys.argv[1], 'r', encoding='utf-8') as f:
    package = json.load(f)

version = package.get('version')
if not version:
    sys.exit(1)
print(version)
PY
}

install_plugin_spec() {
    local plugin_spec="$1"

    runuser -u "$OC_USER" -- env \
        HOME="$OC_HOME" \
        USER="$OC_USER" \
        LOGNAME="$OC_USER" \
        XDG_CONFIG_HOME="$OC_HOME/.config" \
        XDG_CACHE_HOME="$OC_HOME/.cache" \
        XDG_DATA_HOME="$OC_HOME/.local/share" \
        XDG_STATE_HOME="$OC_HOME/.local/state" \
        opencode plugin "$plugin_spec" -g -f
}

log_plugin_installed_version() {
    local plugin_name="$1"
    local plugin_spec installed_version

    plugin_spec=$(plugin_config_spec "$CONFIG_FILE" "$plugin_name" || true)
    if installed_version=$(plugin_installed_version "$plugin_name" "$plugin_spec"); then
        echo "[entrypoint] Plugin '$plugin_name' configured as '$plugin_spec'; installed version $installed_version"
    else
        echo "[entrypoint] Plugin '$plugin_name' configured as '${plugin_spec:-missing}'; installed version unavailable"
    fi
}

ensure_plugin_installed() {
    local plugin_name="$1"
    local plugin_version="$2"
    local desired_spec="${plugin_name}@${plugin_version}"
    local configured_spec installed_version target_spec target_version
    local update_mode="${HOLYCODE_PLUGIN_UPDATE:-manual}"

    if [ "$update_mode" != "auto" ]; then
        update_mode="manual"
    fi

    configured_spec=$(plugin_config_spec "$CONFIG_FILE" "$plugin_name" || true)
    if [ "$update_mode" = "auto" ] || [ -z "$configured_spec" ] || [ "$configured_spec" = "$plugin_name" ]; then
        target_spec="$desired_spec"
    else
        target_spec="$configured_spec"
    fi

    installed_version=$(plugin_installed_version "$plugin_name" "$target_spec" || true)
    target_version=""
    if [ "$target_spec" != "$plugin_name" ]; then
        target_version="${target_spec#"$plugin_name"@}"
    fi

    if [ "$configured_spec" != "$target_spec" ] || \
       [ -z "$installed_version" ] || \
       { [ -n "$target_version" ] && [ "$target_version" != "latest" ] && [ "$installed_version" != "$target_version" ]; }; then
        if [ "$update_mode" = "auto" ] && [ -n "$configured_spec" ]; then
            echo "[entrypoint] Plugin '$plugin_name' syncing to $plugin_version (auto mode)"
        else
            echo "[entrypoint] Plugin '$plugin_name' installing $target_spec"
        fi
        if ! install_plugin_spec "$target_spec"; then
            echo "[entrypoint] WARNING: Failed to install plugin '$target_spec'"
        fi
    fi

    log_plugin_installed_version "$plugin_name"
}

# ---------- UID/GID remapping ----------
PUID="${PUID:-1000}"
PGID="${PGID:-1000}"

CURRENT_UID=$(id -u "$OC_USER")
CURRENT_GID=$(id -g "$OC_USER")

if [ "$PGID" != "$CURRENT_GID" ]; then
    echo "[entrypoint] Changing opencode GID from $CURRENT_GID to $PGID"
    groupmod -o -g "$PGID" opencode
fi

if [ "$PUID" != "$CURRENT_UID" ]; then
    echo "[entrypoint] Changing opencode UID from $CURRENT_UID to $PUID"
    usermod -o -u "$PUID" opencode
fi

# ---------- Fix home directory ownership ----------
chown "$PUID:$PGID" "$OC_HOME"

# Pre-create OpenCode directories (bind mount may start empty)
for dir in \
    "$OC_HOME/.config/opencode" \
    "$OC_HOME/.config/opencode/skills" \
    "$OC_HOME/.local/share/opencode" \
    "$OC_HOME/.local/state/opencode" \
    "$OC_HOME/.cache/opencode" \
    "$OC_HOME/.claude"; do
    mkdir -p "$dir"
    chown "$PUID:$PGID" "$dir"
done
chown "$PUID:$PGID" "$OC_HOME/.config" "$OC_HOME/.local" "$OC_HOME/.local/share" "$OC_HOME/.local/state" "$OC_HOME/.cache" 2>/dev/null || true

# ---------- Ensure /workspace is writable ----------
mkdir -p "$WORKSPACE_DIR"
if ! runuser -u "$OC_USER" -- test -w "$WORKSPACE_DIR"; then
    echo "[entrypoint] /workspace is not writable for $OC_USER, attempting ownership fix"
    chown "$PUID:$PGID" "$WORKSPACE_DIR" 2>/dev/null || true
fi

if ! runuser -u "$OC_USER" -- test -w "$WORKSPACE_DIR"; then
    echo "[entrypoint] WARNING: /workspace is still not writable; fix host ownership or PUID/PGID"
fi

check_cifs_compatibility() {
    [ -d "$OC_HOME" ] || return 0
    local test_db
    test_db=$(mktemp "${OC_HOME}/.holycode-wal-test-XXXXXX.db" 2>/dev/null) || return 0

    if python3 - "$test_db" 2>/dev/null <<'PY'; then
import sqlite3
import sys

db_path = sys.argv[1]
db = sqlite3.connect(db_path)
db.execute('PRAGMA journal_mode=WAL')
db.execute('CREATE TABLE _t (id INTEGER)')
db.execute('INSERT INTO _t VALUES (1)')
db.commit()
db2 = sqlite3.connect(db_path)
db2.execute('SELECT * FROM _t').fetchall()
db2.close()
db.execute('PRAGMA journal_mode=DELETE')
db.close()
PY
        rm -f "$test_db" "${test_db}-wal" "${test_db}-shm" 2>/dev/null || true
        return 0
    fi

    rm -f "$test_db" "${test_db}-wal" "${test_db}-shm" 2>/dev/null || true
    echo ""
    echo "============================================================"
    echo "  WARNING: SQLite WAL locking failed on this mount"
    echo "============================================================"
    echo "  If your data directory is on CIFS/SMB, add 'nobrl,mfsymlinks'"
    echo "  to mount options in /etc/fstab on the host, then remount."
    echo "============================================================"
    echo ""
}

check_cifs_compatibility

# ---------- First-boot bootstrap ----------
SENTINEL="$OC_HOME/.config/opencode/.holycode-bootstrapped"
if [ ! -f "$SENTINEL" ]; then
    echo "[entrypoint] First boot detected, running bootstrap.sh"
    if ! /usr/local/bin/bootstrap.sh; then
        echo "[entrypoint] WARNING: bootstrap.sh failed, continuing anyway"
    fi
fi

sync_shipped_skills

if [ "${ENABLE_HERMES}" = "true" ]; then
    export HERMES_HOME="${HERMES_HOME:-$OC_HOME/.hermes}"
    mkdir -p "$HERMES_HOME"
    chown "$PUID:$PGID" "$HERMES_HOME" 2>/dev/null || true
    touch /etc/s6-overlay/s6-rc.d/user/contents.d/hermes
else
    rm -f /etc/s6-overlay/s6-rc.d/user/contents.d/hermes
fi

if [ "${ENABLE_PAPERCLIP}" = "true" ]; then
    export PAPERCLIP_HOME="${PAPERCLIP_HOME:-$OC_HOME/.paperclip}"
    mkdir -p "$PAPERCLIP_HOME"
    chown "$PUID:$PGID" "$PAPERCLIP_HOME" 2>/dev/null || true
    touch /etc/s6-overlay/s6-rc.d/user/contents.d/paperclip
else
    rm -f /etc/s6-overlay/s6-rc.d/user/contents.d/paperclip
fi

# ---------- Plugin toggles (run every boot for enable/disable) ----------
CONFIG_FILE="$OC_HOME/.config/opencode/opencode.json"
if [ -f "$CONFIG_FILE" ]; then
    # Claude Auth plugin
    if [ "${ENABLE_CLAUDE_AUTH}" = "true" ]; then
        ensure_plugin_installed "$CLAUDE_AUTH_PLUGIN_NAME" "$CLAUDE_AUTH_PLUGIN_VERSION"
    else
        if remove_plugin_config "$CONFIG_FILE" "$CLAUDE_AUTH_PLUGIN_NAME"; then
            echo "[entrypoint] Claude Auth plugin disabled"
        fi
        remove_plugin_config "$OC_HOME/.config/opencode/tui.json" "$CLAUDE_AUTH_PLUGIN_NAME" || true
    fi

    # oh-my-openagent plugin
    if [ "${ENABLE_OH_MY_OPENAGENT}" = "true" ]; then
        ensure_plugin_installed "$OH_MY_OPENAGENT_PLUGIN_NAME" "$OH_MY_OPENAGENT_PLUGIN_VERSION"
    else
        if remove_plugin_config "$CONFIG_FILE" "$OH_MY_OPENAGENT_PLUGIN_NAME"; then
            echo "[entrypoint] oh-my-openagent plugin disabled"
        fi
        remove_plugin_config "$OC_HOME/.config/opencode/tui.json" "$OH_MY_OPENAGENT_PLUGIN_NAME" || true
    fi

    # CLIProxyAPI provider
    CLIPROXYAPI_MARKER="$OC_HOME/.config/opencode/.holycode-cliproxyapi-provider.sha256"
    if ! runuser -u "$OC_USER" -- python3 - "$CONFIG_FILE" "$CLIPROXYAPI_MARKER" "${CLIPROXYAPI_ENABLED:-}" "${CLIPROXYAPI_BASE_URL:-http://cliproxyapi:8317/v1}" "${CLIPROXYAPI_MODEL:-}" "${CLIPROXYAPI_SMALL_MODEL:-}" "${CLIPROXYAPI_API_KEY:+set}" <<'PY'; then
import hashlib
import json
import os
import sys

config_file = sys.argv[1]
marker_file = sys.argv[2]
enabled = sys.argv[3] == 'true'
base_url = sys.argv[4]
model = sys.argv[5]
small_model = sys.argv[6]
api_key_is_set = sys.argv[7] == 'set'
provider_name = 'cliproxyapi'


def provider_hash(provider):
    payload = json.dumps(provider, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def read_marker():
    try:
        with open(marker_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return ''


def write_marker(provider):
    with open(marker_file, 'w', encoding='utf-8') as f:
        f.write(provider_hash(provider))


def remove_marker():
    try:
        os.remove(marker_file)
    except FileNotFoundError:
        pass


def is_holycode_managed(provider):
    marker = read_marker()
    return bool(marker) and provider_hash(provider) == marker


def build_provider():
    provider = {
        'npm': '@ai-sdk/openai-compatible',
        'name': 'CLIProxyAPI',
        'options': {
            'baseURL': base_url,
        },
    }
    if api_key_is_set:
        provider['options']['apiKey'] = '{env:CLIPROXYAPI_API_KEY}'
    models = {}
    if model:
        models[model] = {'name': f'{model} via CLIProxyAPI'}
    if small_model and small_model != model:
        models[small_model] = {'name': f'{small_model} via CLIProxyAPI'}
    if models:
        provider['models'] = models
    return provider


try:
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
except Exception as exc:
    print(f'[entrypoint] WARNING: Skipping CLIProxyAPI provider config: invalid opencode.json ({exc})')
    sys.exit(0)

if not isinstance(config, dict):
    print('[entrypoint] WARNING: Skipping CLIProxyAPI provider config: opencode.json is not an object')
    sys.exit(0)

providers = config.get('provider')
if providers is None:
    providers = {}
elif not isinstance(providers, dict):
    print('[entrypoint] WARNING: Skipping CLIProxyAPI provider config: provider is not an object')
    sys.exit(0)

current = providers.get(provider_name)

if enabled:
    next_provider = build_provider()
    if current is not None and not is_holycode_managed(current):
        remove_marker()
        print('[entrypoint] CLIProxyAPI provider exists (not HolyCode-managed), preserving user config')
        sys.exit(0)
    providers[provider_name] = next_provider
    config['provider'] = providers
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
        f.write('\n')
    write_marker(next_provider)
    if not model:
        print('[entrypoint] WARNING: CLIPROXYAPI_ENABLED=true but CLIPROXYAPI_MODEL is empty')
    print('[entrypoint] CLIProxyAPI provider enabled')
else:
    if current is None:
        remove_marker()
        sys.exit(0)
    if not is_holycode_managed(current):
        remove_marker()
        print('[entrypoint] CLIProxyAPI provider exists (not HolyCode-managed), preserving user config')
        sys.exit(0)
    providers.pop(provider_name, None)
    if providers:
        config['provider'] = providers
    else:
        config.pop('provider', None)
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
        f.write('\n')
    remove_marker()
    print('[entrypoint] CLIProxyAPI provider disabled')
PY
        echo "[entrypoint] WARNING: Failed to update CLIProxyAPI provider config"
    fi
fi

# ---------- Hand off to s6-overlay ----------
echo "[entrypoint] Starting s6-overlay..."
exec /init "$@"
