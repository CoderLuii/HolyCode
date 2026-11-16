#!/usr/bin/env bash
set -euo pipefail

image="${1:?image is required}"
platform="${2:?platform is required}"
release="${3:?release is required}"

docker run --rm --interactive --platform "$platform" --user 0 --entrypoint bash "$image" -s -- "$platform" "$release" <<'SH'
set -euo pipefail
platform="$1"
release="$2"
actual_arch="$(dpkg --print-architecture)"
[ "linux/$actual_arch" = "$platform" ]
apt-get update --error-on=any >/dev/null
for package in chromium chromium-common chromium-sandbox; do
  installed="$(dpkg-query -W -f='${Version}' "$package")"
  available="$(apt-cache policy "$package" | awk '/Candidate:/ {print $2}')"
  [ -n "$installed" ]
  [ -n "$available" ]
  validate-holycode-chromium-version "$installed" "$platform" "$release" "$(date -u +%F)"
  dpkg --compare-versions "$installed" ge "$available"
  printf '%s installed=%s available=%s platform=%s\n' "$package" "$installed" "$available" "$platform"
done
SH
