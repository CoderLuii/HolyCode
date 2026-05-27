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

ensure_plugin_installed() {
    local plugin_name="$1"
    local plugin_dir="$OC_HOME/.cache/opencode/node_modules/$plugin_name"
    local update_mode="${HOLYCODE_PLUGIN_UPDATE:-manual}"

    if [ "$update_mode" != "auto" ]; then
        update_mode="manual"
    fi

    if [ -f "$plugin_dir/package.json" ]; then
        if [ "$update_mode" = "auto" ]; then
            echo "[entrypoint] Plugin '$plugin_name' updating (auto mode)"
            if ! runuser -u "$OC_USER" -- opencode plugin "$plugin_name" -g; then
                echo "[entrypoint] WARNING: Failed to update plugin '$plugin_name'"
            fi
        fi
        return 0
    fi

    echo "[entrypoint] Plugin '$plugin_name' missing, installing"
    if ! runuser -u "$OC_USER" -- opencode plugin "$plugin_name" -g; then
        echo "[entrypoint] WARNING: Failed to install plugin '$plugin_name'"
    fi
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
        if ! grep -q "opencode-claude-auth" "$CONFIG_FILE" 2>/dev/null; then
            runuser -u "$OC_USER" -- python3 - "$CONFIG_FILE" "opencode-claude-auth" 2>/dev/null <<'PY' && echo "[entrypoint] Claude Auth plugin enabled"
import json
import sys

config_file = sys.argv[1]
plugin_name = sys.argv[2]

with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

config.setdefault('plugin', [])
if plugin_name not in config['plugin']:
    config['plugin'].append(plugin_name)

with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2)
PY
        fi
        ensure_plugin_installed "opencode-claude-auth"
    else
        if grep -q "opencode-claude-auth" "$CONFIG_FILE" 2>/dev/null; then
            runuser -u "$OC_USER" -- python3 - "$CONFIG_FILE" "opencode-claude-auth" 2>/dev/null <<'PY' && echo "[entrypoint] Claude Auth plugin disabled"
import json
import sys

config_file = sys.argv[1]
plugin_name = sys.argv[2]

with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

if 'plugin' in config and plugin_name in config['plugin']:
    config['plugin'].remove(plugin_name)

with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2)
PY
        fi
    fi

    # oh-my-openagent plugin
    if [ "${ENABLE_OH_MY_OPENAGENT}" = "true" ]; then
        if ! grep -q "oh-my-openagent" "$CONFIG_FILE" 2>/dev/null; then
            runuser -u "$OC_USER" -- python3 - "$CONFIG_FILE" "oh-my-openagent" 2>/dev/null <<'PY' && echo "[entrypoint] oh-my-openagent plugin enabled"
import json
import sys

config_file = sys.argv[1]
plugin_name = sys.argv[2]

with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

config.setdefault('plugin', [])
if plugin_name not in config['plugin']:
    config['plugin'].append(plugin_name)

with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2)
PY
        fi
        ensure_plugin_installed "oh-my-openagent"
    else
        if grep -q "oh-my-openagent" "$CONFIG_FILE" 2>/dev/null; then
            runuser -u "$OC_USER" -- python3 - "$CONFIG_FILE" "oh-my-openagent" 2>/dev/null <<'PY' && echo "[entrypoint] oh-my-openagent plugin disabled"
import json
import sys

config_file = sys.argv[1]
plugin_name = sys.argv[2]

with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

if 'plugin' in config and plugin_name in config['plugin']:
    config['plugin'].remove(plugin_name)

with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2)
PY
        fi
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
