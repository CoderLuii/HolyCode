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

    if python3 -c "
import sqlite3
db = sqlite3.connect('${test_db}')
db.execute('PRAGMA journal_mode=WAL')
db.execute('CREATE TABLE _t (id INTEGER)')
db.execute('INSERT INTO _t VALUES (1)')
db.commit()
db2 = sqlite3.connect('${test_db}')
db2.execute('SELECT * FROM _t').fetchall()
db2.close()
db.execute('PRAGMA journal_mode=DELETE')
db.close()
" 2>/dev/null; then
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

# ---------- Plugin toggles (run every boot for enable/disable) ----------
CONFIG_FILE="$OC_HOME/.config/opencode/opencode.json"
if [ -f "$CONFIG_FILE" ]; then
    # Claude Auth plugin
    if [ "${ENABLE_CLAUDE_AUTH}" = "true" ]; then
        if ! grep -q "opencode-claude-auth" "$CONFIG_FILE" 2>/dev/null; then
            runuser -u "$OC_USER" -- python3 -c "
import json
with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)
config.setdefault('plugin', [])
if 'opencode-claude-auth' not in config['plugin']:
    config['plugin'].append('opencode-claude-auth')
with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)
" 2>/dev/null && echo "[entrypoint] Claude Auth plugin enabled"
        fi
        ensure_plugin_installed "opencode-claude-auth"
    else
        if grep -q "opencode-claude-auth" "$CONFIG_FILE" 2>/dev/null; then
            runuser -u "$OC_USER" -- python3 -c "
import json
with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)
if 'plugin' in config and 'opencode-claude-auth' in config['plugin']:
    config['plugin'].remove('opencode-claude-auth')
with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)
" 2>/dev/null && echo "[entrypoint] Claude Auth plugin disabled"
        fi
    fi

    # oh-my-openagent plugin
    if [ "${ENABLE_OH_MY_OPENAGENT}" = "true" ]; then
        if ! grep -q "oh-my-openagent" "$CONFIG_FILE" 2>/dev/null; then
            runuser -u "$OC_USER" -- python3 -c "
import json
with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)
config.setdefault('plugin', [])
if 'oh-my-openagent' not in config['plugin']:
    config['plugin'].append('oh-my-openagent')
with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)
" 2>/dev/null && echo "[entrypoint] oh-my-openagent plugin enabled"
        fi
        ensure_plugin_installed "oh-my-openagent"
    else
        if grep -q "oh-my-openagent" "$CONFIG_FILE" 2>/dev/null; then
            runuser -u "$OC_USER" -- python3 -c "
import json
with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)
if 'plugin' in config and 'oh-my-openagent' in config['plugin']:
    config['plugin'].remove('oh-my-openagent')
with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)
" 2>/dev/null && echo "[entrypoint] oh-my-openagent plugin disabled"
        fi
    fi
fi

# ---------- Hand off to s6-overlay ----------
echo "[entrypoint] Starting s6-overlay..."
exec /init "$@"
