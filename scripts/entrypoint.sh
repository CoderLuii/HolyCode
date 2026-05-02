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

# Export proxy API key once for both OpenCode {env:...} and Hermes ${...} expansion.
CLI_PROXY_API_KEY="${CLI_PROXY_API_KEY:-holycode-local}"
export CLI_PROXY_API_KEY

if [ "${ENABLE_CLI_PROXY}" = "true" ]; then
    export CLI_PROXY_HOME="${CLI_PROXY_HOME:-$OC_HOME/.cli-proxy-api}"
    mkdir -p "$CLI_PROXY_HOME"
    chown "$PUID:$PGID" "$CLI_PROXY_HOME" 2>/dev/null || true
    touch /etc/s6-overlay/s6-rc.d/user/contents.d/cli-proxy-api
    mkdir -p /etc/s6-overlay/s6-rc.d/opencode/dependencies.d
    touch /etc/s6-overlay/s6-rc.d/opencode/dependencies.d/cli-proxy-api
else
    rm -f /etc/s6-overlay/s6-rc.d/user/contents.d/cli-proxy-api
    rm -f /etc/s6-overlay/s6-rc.d/opencode/dependencies.d/cli-proxy-api
    # Auto-wire only makes sense when the proxy is running. Force revert if
    # the user disabled the proxy but left CLI_PROXY_AUTOWIRE set.
    CLI_PROXY_AUTOWIRE="false"
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

    # CLI Proxy auto-wire (OpenCode providers)
    CLI_PROXY_AUTOWIRE_SPEC="${CLI_PROXY_AUTOWIRE:-}"
    OC_PROXY_MARKER="$OC_HOME/.config/opencode/.holycode-cli-proxy-managed.json"
    runuser -u "$OC_USER" -- python3 - \
        "$CONFIG_FILE" \
        "$OC_PROXY_MARKER" \
        "CLI_PROXY_API_KEY" \
        "$CLI_PROXY_AUTOWIRE_SPEC" <<'PY'
import json
import os
import sys

config_file, marker_file, api_env_var, spec = sys.argv[1:5]
spec = (spec or "").strip().lower()

oc_targets = {"opencode-anthropic", "opencode-openai", "opencode-google"}
mapping = {
    "opencode-anthropic": ("anthropic", "http://localhost:8317"),
    "opencode-openai":    ("openai",    "http://localhost:8317/v1"),
    "opencode-google":    ("google",    "http://localhost:8317/v1beta"),
}
legacy = {"anthropic": "opencode-anthropic", "openai": "opencode-openai", "google": "opencode-google"}

if spec in ("", "false", "none"):
    requested = set()
elif spec == "all":
    requested = set(oc_targets)
else:
    tokens = [t.strip().lower() for t in spec.split(",") if t.strip()]
    requested = {legacy.get(t, t) for t in tokens}

to_wire = requested & oc_targets

with open(config_file, "r", encoding="utf-8") as f:
    cfg = json.load(f)
cfg.setdefault("provider", {})

prev = []
if os.path.isfile(marker_file):
    try:
        with open(marker_file, "r", encoding="utf-8") as f:
            prev = json.load(f).get("providers", []) or []
    except Exception:
        prev = []

api_ref = "{env:" + api_env_var + "}"

# Revert previously-managed wiring (only when value still matches what we wrote)
for token in prev:
    if token not in mapping:
        continue
    name, base = mapping[token]
    p = cfg["provider"].get(name)
    if not isinstance(p, dict):
        continue
    opts = p.get("options")
    if not isinstance(opts, dict):
        continue
    if opts.get("baseURL") == base:
        opts.pop("baseURL", None)
    if opts.get("apiKey") == api_ref:
        opts.pop("apiKey", None)
    if not opts:
        p.pop("options", None)
    if not p:
        cfg["provider"].pop(name, None)

# Apply new wiring
for token in sorted(to_wire):
    name, base = mapping[token]
    p = cfg["provider"].setdefault(name, {})
    opts = p.setdefault("options", {})
    opts["baseURL"] = base
    opts["apiKey"] = api_ref

with open(config_file, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)

if to_wire:
    os.makedirs(os.path.dirname(marker_file), exist_ok=True)
    with open(marker_file, "w", encoding="utf-8") as f:
        json.dump({"providers": sorted(to_wire)}, f, indent=2)
    print("[entrypoint] CLI Proxy auto-wire (OpenCode): " + ",".join(sorted(to_wire)))
elif os.path.isfile(marker_file):
    os.remove(marker_file)
    if prev:
        print("[entrypoint] CLI Proxy auto-wire (OpenCode): reverted")
PY
fi

# ---------- Hermes auto-wire (only when Hermes is enabled) ----------
if [ "${ENABLE_HERMES}" = "true" ]; then
    HERMES_HOME="${HERMES_HOME:-$OC_HOME/.hermes}"
    HERMES_CONFIG="$HERMES_HOME/config.yaml"
    HERMES_TEMPLATE="/usr/local/share/holycode/hermes/config.example.yaml"
    HERMES_PROVIDER="${CLI_PROXY_HERMES_PROVIDER:-anthropic}"
    runuser -u "$OC_USER" -- python3 - \
        "$HERMES_CONFIG" \
        "$HERMES_TEMPLATE" \
        "CLI_PROXY_API_KEY" \
        "${CLI_PROXY_AUTOWIRE:-}" \
        "$HERMES_PROVIDER" <<'PY'
import os
import sys

import yaml

config_file, template_file, api_env_var, spec, provider = sys.argv[1:6]
spec = (spec or "").strip().lower()
provider = (provider or "anthropic").strip().lower()

provider_paths = {
    "anthropic": "http://localhost:8317",
    "openai":    "http://localhost:8317/v1",
    "google":    "http://localhost:8317/v1beta",
}
if provider not in provider_paths:
    provider = "anthropic"
base_url = provider_paths[provider]
api_ref = "${" + api_env_var + "}"

legacy = {"anthropic": "opencode-anthropic", "openai": "opencode-openai", "google": "opencode-google"}
if spec in ("", "false", "none"):
    requested = set()
elif spec == "all":
    requested = {"opencode-anthropic", "opencode-openai", "opencode-google", "hermes"}
else:
    tokens = [t.strip().lower() for t in spec.split(",") if t.strip()]
    requested = {legacy.get(t, t) for t in tokens}
wire_hermes = "hermes" in requested

if wire_hermes:
    if not os.path.isfile(config_file):
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(template_file, "r", encoding="utf-8") as src:
            with open(config_file, "w", encoding="utf-8") as dst:
                dst.write(src.read())

    with open(config_file, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    cfg.setdefault("model", {})
    cfg["model"]["provider"] = provider
    cfg["model"]["base_url"] = base_url
    cfg["model"]["api_key"] = api_ref

    cfg.setdefault("auxiliary", {})
    for aux in ("vision", "web_extract", "compression"):
        cfg["auxiliary"].setdefault(aux, {})
        cfg["auxiliary"][aux]["base_url"] = base_url
        cfg["auxiliary"][aux]["api_key"] = api_ref

    cfg["_holycode_cli_proxy_managed"] = {
        "applied_provider": provider,
        "applied_base_url": base_url,
        "applied_api_ref": api_ref,
    }

    with open(config_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)
    print("[entrypoint] CLI Proxy auto-wire (Hermes): provider=" + provider)
elif os.path.isfile(config_file):
    with open(config_file, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    sentinel = cfg.get("_holycode_cli_proxy_managed")
    if isinstance(sentinel, dict):
        prev_provider = sentinel.get("applied_provider", "anthropic")
        prev_base = sentinel.get("applied_base_url", provider_paths.get(prev_provider, ""))
        prev_api = sentinel.get("applied_api_ref", api_ref)

        model = cfg.get("model")
        if isinstance(model, dict):
            if model.get("provider") == prev_provider:
                model.pop("provider", None)
            if model.get("base_url") == prev_base:
                model.pop("base_url", None)
            if model.get("api_key") == prev_api:
                model.pop("api_key", None)

        aux_root = cfg.get("auxiliary", {})
        for aux in ("vision", "web_extract", "compression"):
            aux_cfg = aux_root.get(aux)
            if not isinstance(aux_cfg, dict):
                continue
            if aux_cfg.get("base_url") == prev_base:
                aux_cfg.pop("base_url", None)
            if aux_cfg.get("api_key") == prev_api:
                aux_cfg.pop("api_key", None)

        cfg.pop("_holycode_cli_proxy_managed", None)
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f, sort_keys=False)
        print("[entrypoint] CLI Proxy auto-wire (Hermes): reverted")
PY
fi

# ---------- Hand off to s6-overlay ----------
echo "[entrypoint] Starting s6-overlay..."
exec /init "$@"
