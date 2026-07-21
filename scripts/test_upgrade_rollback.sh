#!/usr/bin/env bash
set -euo pipefail

current_image="${1:?usage: scripts/test_upgrade_rollback.sh <current-image> <previous-image> [platform]}"
previous_image="${2:?usage: scripts/test_upgrade_rollback.sh <current-image> <previous-image> [platform]}"
platform="${3:-linux/amd64}"
prefix="holycode-upgrade-$$"
baseline_name="${prefix}-baseline"
upgrade_name="${prefix}-current"
rollback_name="${prefix}-rollback"
baseline_home="${prefix}-baseline-home"
baseline_workspace="${prefix}-baseline-workspace"
upgrade_home="${prefix}-upgrade-home"
upgrade_workspace="${prefix}-upgrade-workspace"

current_node_version="$(docker run --rm --platform "$platform" --entrypoint node "$current_image" --version)"
previous_node_version="$(docker run --rm --platform "$platform" --entrypoint node "$previous_image" --version)"

# Git for Windows may rewrite Linux paths even when MSYSTEM is not exported.
export MSYS_NO_PATHCONV=1

cleanup() {
  docker rm -f "$baseline_name" "$upgrade_name" "$rollback_name" >/dev/null 2>&1 || true
  docker volume rm \
    "$baseline_home" "$baseline_workspace" \
    "$upgrade_home" "$upgrade_workspace" >/dev/null 2>&1 || true
}
trap cleanup EXIT

wait_for_services() {
  local name="$1"
  local expect_hermes="$2"

  for _ in $(seq 1 180); do
    if docker exec "$name" curl -fsS --max-time 5 -o /dev/null http://localhost:4096/ 2>/dev/null && \
       docker exec "$name" curl -fsS --max-time 5 -o /dev/null http://localhost:3100/api/health 2>/dev/null; then
      if [ "$expect_hermes" != "true" ] || docker exec "$name" curl -fsS --max-time 5 -o /dev/null \
         -H 'Authorization: Bearer holycode-upgrade-test-key' \
         http://localhost:8642/v1/models 2>/dev/null; then
        return 0
      fi
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

start_stack() {
  local name="$1"
  local image="$2"
  local home_volume="$3"
  local workspace_volume="$4"
  local enable_hermes="$5"

  docker run -d --platform "$platform" --name "$name" \
    -v "$home_volume:/home/opencode" \
    -v "$workspace_volume:/workspace" \
    -e PUID=2345 \
    -e PGID=2345 \
    -e ENABLE_PAPERCLIP=true \
    -e ENABLE_HERMES="$enable_hermes" \
    -e API_SERVER_KEY=holycode-upgrade-test-key \
    -e CLIPROXYAPI_ENABLED=true \
    -e CLIPROXYAPI_MODEL=holycode-upgrade-model \
    -e CLIPROXYAPI_API_KEY=holycode-upgrade-provider-key \
    "$image" >/dev/null
  wait_for_services "$name" "$enable_hermes"
}

clone_volume() {
  local source_volume="$1"
  local target_volume="$2"

  docker volume create "$target_volume" >/dev/null
  docker run --rm --platform "$platform" --entrypoint sh \
    -v "$source_volume:/from:ro" \
    -v "$target_volume:/to" \
    "$current_image" -lc 'cp -a /from/. /to/'
}

assert_persisted_state() {
  local name="$1"

  docker exec "$name" test -f /home/opencode/.claude/holycode-upgrade-auth-marker
  docker exec "$name" test -f /home/opencode/.hermes/holycode-upgrade-marker
  docker exec "$name" test -f /home/opencode/.paperclip/instances/default/data/holycode-upgrade-marker
  docker exec "$name" test -f /workspace/holycode-upgrade-marker
  docker exec "$name" grep -Fq 'holycode-upgrade-model' /home/opencode/.config/opencode/opencode.json
  [ "$(docker exec "$name" stat -c %u /workspace/holycode-upgrade-marker)" = "2345" ]
}

docker pull --platform "$platform" "$previous_image" >/dev/null
docker volume create "$baseline_home" >/dev/null
docker volume create "$baseline_workspace" >/dev/null

start_stack "$baseline_name" "$previous_image" "$baseline_home" "$baseline_workspace" true
docker exec -u opencode "$baseline_name" sh -lc '
  touch /home/opencode/.claude/holycode-upgrade-auth-marker
  touch /home/opencode/.hermes/holycode-upgrade-marker
  touch /home/opencode/.paperclip/instances/default/data/holycode-upgrade-marker
  touch /workspace/holycode-upgrade-marker
'
assert_persisted_state "$baseline_name"
docker rm -f "$baseline_name" >/dev/null

clone_volume "$baseline_home" "$upgrade_home"
clone_volume "$baseline_workspace" "$upgrade_workspace"

start_stack "$upgrade_name" "$current_image" "$upgrade_home" "$upgrade_workspace" false
assert_persisted_state "$upgrade_name"
docker exec "$upgrade_name" node --version | grep -Fx "$current_node_version"
docker restart "$upgrade_name" >/dev/null
wait_for_services "$upgrade_name" false
assert_persisted_state "$upgrade_name"
docker rm -f "$upgrade_name" >/dev/null

start_stack "$rollback_name" "$previous_image" "$baseline_home" "$baseline_workspace" true
assert_persisted_state "$rollback_name"
docker exec "$rollback_name" node --version | grep -Fx "$previous_node_version"

echo "upgrade and rollback validation passed for $platform"
