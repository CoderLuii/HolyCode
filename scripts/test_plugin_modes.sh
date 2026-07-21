#!/usr/bin/env bash
set -euo pipefail

image="${1:?usage: scripts/test_plugin_modes.sh <image>}"
name="holycode-plugin-modes-$$"
volume="${name}-home"

# Git for Windows may rewrite Linux paths even when MSYSTEM is not exported.
export MSYS_NO_PATHCONV=1

cleanup() {
  docker rm -f "$name" >/dev/null 2>&1 || true
  docker volume rm "$volume" >/dev/null 2>&1 || true
}
trap cleanup EXIT

wait_for_opencode() {
  for _ in $(seq 1 180); do
    if docker exec "$name" curl -fsS --max-time 5 -o /dev/null http://localhost:4096/ 2>/dev/null; then
      return 0
    fi
    if [ "$(docker inspect -f '{{.State.Running}}' "$name" 2>/dev/null || true)" != "true" ]; then
      docker logs "$name" || true
      return 1
    fi
    sleep 2
  done
  docker logs "$name" || true
  return 1
}

wait_for_log() {
  local message="$1"

  for _ in $(seq 1 30); do
    if docker logs "$name" 2>&1 | grep -Fq "$message"; then
      return 0
    fi
    sleep 1
  done
  docker logs "$name" >&2 || true
  echo "missing expected startup log: $message" >&2
  return 1
}

run_with_plugins() {
  local mode="$1"

  docker run -d --name "$name" \
    -v "$volume:/home/opencode" \
    -e ENABLE_CLAUDE_AUTH=true \
    -e ENABLE_OH_MY_OPENAGENT=true \
    -e "HOLYCODE_PLUGIN_UPDATE=$mode" \
    "$image" >/dev/null
  wait_for_opencode
}

assert_plugin() {
  local plugin_name="$1"
  local plugin_version="$2"
  local package_json="/home/opencode/.cache/opencode/packages/${plugin_name}@${plugin_version}/node_modules/${plugin_name}/package.json"

  docker exec "$name" grep -Fq "\"${plugin_name}@${plugin_version}\"" /home/opencode/.config/opencode/opencode.json
  [ "$(docker exec "$name" node -p "require('$package_json').version")" = "$plugin_version" ]
}

docker volume create "$volume" >/dev/null
run_with_plugins manual
assert_plugin opencode-claude-auth 2.0.0
assert_plugin oh-my-openagent 4.19.0
wait_for_log "configured as 'opencode-claude-auth@2.0.0'; installed version 2.0.0"
wait_for_log "configured as 'oh-my-openagent@4.19.0'; installed version 4.19.0"

docker exec -u opencode \
  -e HOME=/home/opencode \
  -e USER=opencode \
  -e LOGNAME=opencode \
  -e XDG_CONFIG_HOME=/home/opencode/.config \
  -e XDG_CACHE_HOME=/home/opencode/.cache \
  -e XDG_DATA_HOME=/home/opencode/.local/share \
  -e XDG_STATE_HOME=/home/opencode/.local/state \
  "$name" opencode plugin opencode-claude-auth@1.5.4 -g -f >/dev/null

docker restart "$name" >/dev/null
wait_for_opencode
assert_plugin opencode-claude-auth 1.5.4

docker rm -f "$name" >/dev/null
run_with_plugins auto
assert_plugin opencode-claude-auth 2.0.0
wait_for_log "Plugin 'opencode-claude-auth' syncing to 2.0.0 (auto mode)"

docker rm -f "$name" >/dev/null
run_with_plugins manual
docker exec "$name" sed -i 's/opencode-claude-auth@2.0.0/opencode-claude-auth/' \
  /home/opencode/.config/opencode/opencode.json
docker restart "$name" >/dev/null
wait_for_opencode
assert_plugin opencode-claude-auth 2.0.0
wait_for_log "Plugin 'opencode-claude-auth' installing opencode-claude-auth@2.0.0"

docker rm -f "$name" >/dev/null
docker run -d --name "$name" -v "$volume:/home/opencode" "$image" >/dev/null
wait_for_opencode
if docker exec "$name" grep -Eq 'opencode-claude-auth|oh-my-openagent' /home/opencode/.config/opencode/opencode.json; then
  echo "disabled plugin remains in opencode.json" >&2
  exit 1
fi
if docker exec "$name" sh -lc "test -f /home/opencode/.config/opencode/tui.json && grep -Eq 'opencode-claude-auth|oh-my-openagent' /home/opencode/.config/opencode/tui.json"; then
  echo "disabled plugin remains in tui.json" >&2
  exit 1
fi

echo "plugin mode validation passed"
