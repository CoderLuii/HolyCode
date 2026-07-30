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
CLAUDE_AUTH_PLUGIN_VERSION="2.1.5"
CLAUDE_AUTH_PLUGIN_SOURCE="/usr/local/share/holycode/plugins/opencode-claude-auth"

sync_shipped_skills() {
    local source_skills_dir="/usr/local/share/holycode/skills"
    local target_skills_dir="$OC_HOME/.config/opencode/skills"

    [ -d "$source_skills_dir" ] || return 0

    mkdir -p "$target_skills_dir"
    chown "$PUID:$PGID" "$target_skills_dir"

    find "$source_skills_dir" -mindepth 1 -maxdepth 1 -type d | while read -r skill_dir; do
        local skill_name target_dir
        skill_name=$(basename "$skill_dir")
        target_dir="$target_skills_dir/$skill_name"

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

migrate_oh_my_openagent_config() {
    local config_file="$1"
    local tui_config_file="$OC_HOME/.config/opencode/tui.json"
    local plugin_name="oh-my-openagent"
    local marker_file="$OC_HOME/.config/opencode/.holycode-oh-my-openagent-migrated-v1.1.4"
    local config_spec tui_spec plugin_spec
    local removed=0

    config_spec="$(plugin_config_spec "$config_file" "$plugin_name" || true)"
    tui_spec="$(plugin_config_spec "$tui_config_file" "$plugin_name" || true)"
    plugin_spec="${config_spec:-$tui_spec}"
    [ -n "$plugin_spec" ] || return 0

    if [ -f "$marker_file" ]; then
        echo "[entrypoint] WARNING: '$plugin_spec' was added after the v1.1.4 migration and is user-managed."
        echo "[entrypoint] HolyCode will not install or update it. Remove it from your OpenCode configuration to disable it."
        return 0
    fi

    if [ -n "$config_spec" ]; then
        remove_plugin_config "$config_file" "$plugin_name"
        removed=1
    fi
    if [ -n "$tui_spec" ]; then
        remove_plugin_config "$tui_config_file" "$plugin_name"
        removed=1
    fi

    if [ "$removed" -eq 1 ]; then
        runuser -u "$OC_USER" -- python3 - "$marker_file" "$plugin_spec" <<'PY'
from pathlib import Path
import sys

Path(sys.argv[1]).write_text(f"{sys.argv[2]}\n", encoding="utf-8")
PY
        echo "[entrypoint] Disabled legacy HolyCode-managed '$plugin_spec' configuration."
        echo "[entrypoint] Its package cache and settings were preserved; add it back manually to accept the current upstream risk."
    fi
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

set_plugin_config() {
    local config_file="$1"
    local plugin_name="$2"
    local plugin_spec="$3"

    runuser -u "$OC_USER" -- python3 - "$config_file" "$plugin_name" "$plugin_spec" <<'PY'
import json
import sys

config_file, plugin_name, plugin_spec = sys.argv[1:]
with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

plugins = config.get('plugin', [])
if not isinstance(plugins, list):
    plugins = []
plugins = [
    plugin
    for plugin in plugins
    if not (
        isinstance(plugin, str)
        and (plugin == plugin_name or plugin.startswith(f'{plugin_name}@'))
    )
]
plugins.append(plugin_spec)
config['plugin'] = plugins

with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2)
    f.write('\n')
PY
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

install_offline_claude_auth() {
    local plugin_name="$CLAUDE_AUTH_PLUGIN_NAME"
    local plugin_version="$CLAUDE_AUTH_PLUGIN_VERSION"
    local desired_spec="${plugin_name}@${plugin_version}"
    local configured_spec installed_version target_spec target_version
    local update_mode="${HOLYCODE_PLUGIN_UPDATE:-manual}"
    local package_root package_dir

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

    if [ "$update_mode" = "manual" ] && [ "$target_spec" != "$desired_spec" ] && \
       [ -n "$installed_version" ] && [ "$installed_version" = "$target_version" ]; then
        echo "[entrypoint] Plugin '$plugin_name' remains at '$target_spec' (manual mode)"
        log_plugin_installed_version "$plugin_name"
        return 0
    fi

    if [ "$configured_spec" != "$target_spec" ] || \
       [ -z "$installed_version" ] || \
       { [ -n "$target_version" ] && [ "$target_version" != "latest" ] && [ "$installed_version" != "$target_version" ]; }; then
        if [ "$target_spec" != "$desired_spec" ]; then
            echo "[entrypoint] Plugin '$plugin_name' remains at '$target_spec' (manual mode); no matching offline payload is bundled"
            log_plugin_installed_version "$plugin_name"
            return 0
        fi
        if [ "$update_mode" = "auto" ] && [ -n "$configured_spec" ]; then
            echo "[entrypoint] Plugin '$plugin_name' syncing to $plugin_version (auto mode)"
        else
            echo "[entrypoint] Plugin '$plugin_name' installing $target_spec"
        fi
        package_root="$OC_HOME/.cache/opencode/packages/$target_spec/node_modules"
        package_dir="$package_root/$plugin_name"
        rm -rf "$package_dir"
        mkdir -p "$package_root"
        cp -a "$CLAUDE_AUTH_PLUGIN_SOURCE" "$package_dir"
        chown -R "$PUID:$PGID" "$OC_HOME/.cache/opencode/packages/$target_spec"
        set_plugin_config "$CONFIG_FILE" "$plugin_name" "$target_spec"
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
    echo "[entrypoint] ERROR: The bundled Hermes is temporarily unavailable in v1.1.4 because its pinned dependencies have unresolved security updates." >&2
    echo "[entrypoint] Your /home/opencode/.hermes is preserved. Remove ENABLE_HERMES=true to start HolyCode, or run Hermes separately until bundling returns." >&2
    exit 1
fi

if [ "${ENABLE_OH_MY_OPENAGENT}" = "true" ]; then
    echo "[entrypoint] ERROR: HolyCode-managed oh-my-openagent installation is unavailable in v1.1.4." >&2
    echo "[entrypoint] Your existing configuration and data were not changed. Remove ENABLE_OH_MY_OPENAGENT=true to start HolyCode, then manage the plugin directly if you accept its current upstream risk." >&2
    exit 1
fi

if [ "${ENABLE_PAPERCLIP}" = "true" ]; then
    export PAPERCLIP_HOME="${PAPERCLIP_HOME:-$OC_HOME/.paperclip}"
    mkdir -p "$PAPERCLIP_HOME"
    chown "$PUID:$PGID" "$PAPERCLIP_HOME" 2>/dev/null || true
    touch /etc/s6-overlay/user-bundles.d/user/contents.d/paperclip
else
    rm -f /etc/s6-overlay/user-bundles.d/user/contents.d/paperclip
fi

# ---------- Plugin toggles (run every boot for enable/disable) ----------
CONFIG_FILE="$OC_HOME/.config/opencode/opencode.json"
if [ -f "$CONFIG_FILE" ]; then
    migrate_oh_my_openagent_config "$CONFIG_FILE"

    # Claude Auth plugin
    if [ "${ENABLE_CLAUDE_AUTH}" = "true" ]; then
        install_offline_claude_auth
    else
        if remove_plugin_config "$CONFIG_FILE" "$CLAUDE_AUTH_PLUGIN_NAME"; then
            echo "[entrypoint] Claude Auth plugin disabled"
        fi
        remove_plugin_config "$OC_HOME/.config/opencode/tui.json" "$CLAUDE_AUTH_PLUGIN_NAME" || true
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
