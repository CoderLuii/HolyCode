#!/usr/bin/env bash
set -euo pipefail

version="${1:?usage: validate_chromium_version.sh <version> <platform> <release> <as-of>}"
platform="${2:?platform is required}"
release="${3:?release is required}"
as_of="${4:?as-of date is required}"
floor="154.0.8037.92-1~deb13u1"

case "$as_of" in
  ????-??-??) ;;
  *) exit 1 ;;
esac
date -d "$as_of" +%F 2>/dev/null | grep -Fx "$as_of" >/dev/null
case "$platform" in
  linux/amd64|linux/arm64) ;;
  *) exit 1 ;;
esac
[[ "$release" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]

dpkg --compare-versions "$version" ge "$floor"
