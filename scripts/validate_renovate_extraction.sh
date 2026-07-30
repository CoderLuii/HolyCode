#!/usr/bin/env bash
set -euo pipefail

renovate_version="${1:-44.2.3}"
log_file=$(mktemp)
trap 'rm -f "$log_file"' EXIT

npx --yes --package "renovate@${renovate_version}" \
  renovate-config-validator --strict renovate.json
if ! LOG_LEVEL=debug npx --yes --package "renovate@${renovate_version}" \
  renovate --platform=local --dry-run=extract >"$log_file" 2>&1; then
  cat "$log_file" >&2
  exit 1
fi

grep -Eq '"packageFile"[[:space:]]*:[[:space:]]*"config/python-requirements.in"' "$log_file"
grep -Eq '"config/python-requirements.lock"' "$log_file"
grep -Eq '"packageFile"[[:space:]]*:[[:space:]]*"config/python-seed-requirements.in"' "$log_file"
grep -Eq '"config/python-seed-requirements.lock"' "$log_file"

if grep -Fq 'Manager explicitly enabled in "enabledManagers" config, but found no results.' "$log_file"; then
  cat "$log_file" >&2
  exit 1
fi

echo "Renovate extraction validation passed"
