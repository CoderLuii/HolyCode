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

run_with_auth() {
  local mode="$1"

  docker run -d --name "$name" \
    --network none \
    -v "$volume:/home/opencode" \
    -e ENABLE_CLAUDE_AUTH=true \
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
run_with_auth manual
assert_plugin opencode-claude-auth 2.1.6
wait_for_log "configured as 'opencode-claude-auth@2.1.6'; installed version 2.1.6"

docker exec "$name" sh -lc '
  set -eu
  old_root=/home/opencode/.cache/opencode/packages/opencode-claude-auth@1.5.4/node_modules/opencode-claude-auth
  mkdir -p "$old_root"
  printf "{\"name\":\"opencode-claude-auth\",\"version\":\"1.5.4\"}\n" > "$old_root/package.json"
  sed -i "s/opencode-claude-auth@2.1.6/opencode-claude-auth@1.5.4/" \
    /home/opencode/.config/opencode/opencode.json
  chown -R opencode:opencode /home/opencode/.cache/opencode/packages/opencode-claude-auth@1.5.4
'

docker restart "$name" >/dev/null
wait_for_opencode
assert_plugin opencode-claude-auth 1.5.4
wait_for_log "remains at 'opencode-claude-auth@1.5.4' (manual mode)"

docker rm -f "$name" >/dev/null
run_with_auth auto
assert_plugin opencode-claude-auth 2.1.6
wait_for_log "Plugin 'opencode-claude-auth' syncing to 2.1.6 (auto mode)"

docker rm -f "$name" >/dev/null
run_with_auth manual
docker exec "$name" sed -i 's/opencode-claude-auth@2.1.6/opencode-claude-auth/' \
  /home/opencode/.config/opencode/opencode.json
docker restart "$name" >/dev/null
wait_for_opencode
assert_plugin opencode-claude-auth 2.1.6
wait_for_log "Plugin 'opencode-claude-auth' installing opencode-claude-auth@2.1.6"

docker rm -f "$name" >/dev/null
docker run -d --name "$name" --network none -v "$volume:/home/opencode" "$image" >/dev/null
wait_for_opencode
if docker exec "$name" grep -Eq 'opencode-claude-auth' /home/opencode/.config/opencode/opencode.json; then
  echo "disabled plugin remains in opencode.json" >&2
  exit 1
fi
if docker exec "$name" sh -lc "test -f /home/opencode/.config/opencode/tui.json && grep -Eq 'opencode-claude-auth' /home/opencode/.config/opencode/tui.json"; then
  echo "disabled plugin remains in tui.json" >&2
  exit 1
fi

docker exec -i "$name" python3 - <<'PY'
import json
from pathlib import Path

config_path = Path("/home/opencode/.config/opencode/opencode.json")
config = json.loads(config_path.read_text())
config.setdefault("plugin", []).append("oh-my-openagent@4.19.0")
config_path.write_text(json.dumps(config, indent=2) + "\n")
tui_path = Path("/home/opencode/.config/opencode/tui.json")
tui_path.write_text(
    json.dumps({"plugin": ["oh-my-openagent@4.19.0"]}, indent=2) + "\n"
)
for path in (
    Path("/home/opencode/.config/opencode/oh-my-openagent.jsonc"),
    Path("/home/opencode/.cache/opencode/oh-my-openagent-preserved"),
    Path("/home/opencode/.config/opencode/skills/oh-my-openagent-setup/preserved"),
    Path("/home/opencode/.cache/opencode/packages/oh-my-openagent@4.19.0/node_modules/oh-my-openagent/package.json"),
):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '{"name":"oh-my-openagent","version":"4.19.0"}\n'
        if path.name == "package.json"
        else "preserved\n"
    )
PY
docker exec "$name" chown opencode:opencode \
  /home/opencode/.config/opencode/tui.json
docker rm -f "$name" >/dev/null

if docker run --rm --network none -v "$volume:/home/opencode" \
  -e ENABLE_OH_MY_OPENAGENT=true "$image" >/tmp/holycode-oh-my-openagent.log 2>&1; then
  echo "ENABLE_OH_MY_OPENAGENT=true unexpectedly started" >&2
  exit 1
fi
grep -F "HolyCode-managed oh-my-openagent installation is unavailable" /tmp/holycode-oh-my-openagent.log
grep -F "existing configuration and data were not changed" /tmp/holycode-oh-my-openagent.log
docker run -d --name "$name" --network none -v "$volume:/home/opencode" "$image" >/dev/null
wait_for_opencode
wait_for_log "Disabled legacy HolyCode-managed 'oh-my-openagent@4.19.0' configuration"
docker run --rm --entrypoint sh -v "$volume:/home/opencode" "$image" -lc '
  ! grep -F "oh-my-openagent@4.19.0" /home/opencode/.config/opencode/opencode.json
  ! grep -F "oh-my-openagent@4.19.0" /home/opencode/.config/opencode/tui.json
  grep -Fx "oh-my-openagent@4.19.0" \
    /home/opencode/.config/opencode/.holycode-oh-my-openagent-migrated-v1.1.4
  test -f /home/opencode/.config/opencode/oh-my-openagent.jsonc
  test -f /home/opencode/.cache/opencode/oh-my-openagent-preserved
  test -f /home/opencode/.config/opencode/skills/oh-my-openagent-setup/preserved
  test -f /home/opencode/.cache/opencode/packages/oh-my-openagent@4.19.0/node_modules/oh-my-openagent/package.json
'
docker rm -f "$name" >/dev/null
docker run --rm --entrypoint sh -v "$volume:/home/opencode" "$image" -lc '
  rm /home/opencode/.config/opencode/.holycode-oh-my-openagent-migrated-v1.1.4
  printf "{\"plugin\":[\"oh-my-openagent@4.19.0\"]}\n" \
    > /home/opencode/.config/opencode/tui.json
  chown opencode:opencode /home/opencode/.config/opencode/tui.json
'
docker run -d --name "$name" --network none -v "$volume:/home/opencode" "$image" >/dev/null
wait_for_opencode
wait_for_log "Disabled legacy HolyCode-managed 'oh-my-openagent@4.19.0' configuration"
docker exec "$name" sh -lc '
  ! grep -F "oh-my-openagent@4.19.0" /home/opencode/.config/opencode/opencode.json
  ! grep -F "oh-my-openagent@4.19.0" /home/opencode/.config/opencode/tui.json
  grep -Fx "oh-my-openagent@4.19.0" \
    /home/opencode/.config/opencode/.holycode-oh-my-openagent-migrated-v1.1.4
'
docker exec -i "$name" python3 - <<'PY'
import json
from pathlib import Path

config_path = Path("/home/opencode/.config/opencode/opencode.json")
config = json.loads(config_path.read_text())
config.setdefault("plugin", []).append("oh-my-openagent@4.19.0")
config_path.write_text(json.dumps(config, indent=2) + "\n")
PY
docker restart "$name" >/dev/null
wait_for_opencode
wait_for_log "'oh-my-openagent@4.19.0' was added after the v1.1.4 migration and is user-managed"
docker exec "$name" grep -F "oh-my-openagent@4.19.0" \
  /home/opencode/.config/opencode/opencode.json
docker rm -f "$name" >/dev/null

echo "plugin mode validation passed"
