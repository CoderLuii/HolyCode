#!/usr/bin/env bash
set -euo pipefail

image="${1:?usage: scripts/test_claude_auth.sh <image> <host-home>}"
host_home="${2:?usage: scripts/test_claude_auth.sh <image> <host-home>}"
credentials="$host_home/.claude/.credentials.json"
settings="$host_home/.claude.json"
volume="holycode-claude-auth-$$"

test -f "$credentials"
test -f "$settings"

# Keep Git for Windows from rewriting container-side bind mount paths.
export MSYS_NO_PATHCONV=1

cleanup() {
  docker volume rm "$volume" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker volume create "$volume" >/dev/null
docker run --rm --entrypoint sh \
  -v "$credentials:/source/credentials.json:ro" \
  -v "$settings:/source/claude.json:ro" \
  -v "$volume:/home/opencode" \
  "$image" -lc '
    mkdir -p /home/opencode/.claude
    cp /source/credentials.json /home/opencode/.claude/.credentials.json
    cp /source/claude.json /home/opencode/.claude.json
    chown -R opencode:opencode /home/opencode/.claude /home/opencode/.claude.json
    sha256sum /home/opencode/.claude/.credentials.json /home/opencode/.claude.json > /home/opencode/.claude-auth-before
  '

for _ in 1 2; do
  docker run --rm --entrypoint sh \
    -v "$volume:/home/opencode" \
    "$image" -lc '
      runuser -u opencode -- claude auth status --json |
        jq -e ".loggedIn == true and (.authMethod | length > 0)" >/dev/null
    '
done

docker run --rm --entrypoint sh \
  -v "$volume:/home/opencode" \
  "$image" -lc '
    sha256sum --check --status /home/opencode/.claude-auth-before
  '

echo "Claude authentication and recreation persistence passed"
