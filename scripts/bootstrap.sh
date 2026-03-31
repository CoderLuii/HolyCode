#!/bin/bash
set -e

# ==============================================================================
# HolyCode - First-Boot Bootstrap
# Runs once on first container start, then creates a sentinel to skip next time.
# Delete ~/.config/opencode/.holycode-bootstrapped to re-trigger.
# ==============================================================================

OC_HOME="/home/opencode"
OC_USER="opencode"
PUID="${PUID:-1000}"
PGID="${PGID:-1000}"
SOURCE_DIR="/usr/local/share/holycode"

echo "[bootstrap] Running first-boot initialization..."

# ---------- Copy default opencode.json ----------
if [ ! -f "$OC_HOME/.config/opencode/opencode.json" ]; then
    cp "$SOURCE_DIR/opencode.json" "$OC_HOME/.config/opencode/opencode.json"
    echo "[bootstrap] Copied default opencode.json"
else
    echo "[bootstrap] opencode.json already exists, skipping"
fi

# ---------- Git configuration ----------
GIT_USER_NAME="${GIT_USER_NAME:-HolyCode User}"
GIT_USER_EMAIL="${GIT_USER_EMAIL:-noreply@holycode.local}"
runuser -u "$OC_USER" -- git config --global safe.directory /workspace
runuser -u "$OC_USER" -- git config --global user.name "$GIT_USER_NAME"
runuser -u "$OC_USER" -- git config --global user.email "$GIT_USER_EMAIL"
echo "[bootstrap] Configured git as '$GIT_USER_NAME <$GIT_USER_EMAIL>'"

# ---------- Fix ownership ----------
chown -R "$PUID:$PGID" "$OC_HOME/.config/opencode"
chown -R "$PUID:$PGID" "$OC_HOME/.local/share/opencode"
chown -R "$PUID:$PGID" "$OC_HOME/.local/state/opencode"
chown -R "$PUID:$PGID" "$OC_HOME/.cache/opencode"

# ---------- Create sentinel ----------
touch "$OC_HOME/.config/opencode/.holycode-bootstrapped"
chown "$PUID:$PGID" "$OC_HOME/.config/opencode/.holycode-bootstrapped"

echo "[bootstrap] First-boot initialization complete."
