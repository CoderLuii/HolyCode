#!/usr/bin/env bash
set -euo pipefail

version="${1:?usage: validate_chromium_version.sh <version> <platform> <release> <as-of>}"
platform="${2:?platform is required}"
release="${3:?release is required}"
as_of="${4:?as-of date is required}"
floor="154.0.8037.92-1~deb13u1"
review_date="2026-10-01"
expiry="2026-10-08"

case "$as_of" in
  ????-??-??) ;;
  *) exit 1 ;;
esac
date -d "$as_of" +%F 2>/dev/null | grep -Fx "$as_of" >/dev/null

if [ "$version" = "154.0.8037.57-1~deb13u1" ] && \
  [ "$platform" = "linux/arm64" ] && \
  [ "$release" = "v1.2.4" ]; then
  [ "$as_of" = "$review_date" ] || [ "$as_of" \> "$review_date" ]
  [ "$as_of" = "$expiry" ] || [ "$as_of" \< "$expiry" ]
  exit
fi

dpkg --compare-versions "$version" ge "$floor"
