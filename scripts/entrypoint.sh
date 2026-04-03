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
