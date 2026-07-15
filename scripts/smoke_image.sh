#!/usr/bin/env bash
set -euo pipefail

image="${1:?usage: scripts/smoke_image.sh <image>}"

image_label() {
  docker inspect --format "{{ index .Config.Labels \"$1\" }}" "$image"
}

expected_opencode="$(image_label io.holycode.version.opencode)"
expected_claude="$(image_label io.holycode.version.claude-code)"
expected_paperclip="$(image_label io.holycode.version.paperclip)"
expected_npm="$(image_label io.holycode.version.npm)"
expected_typescript="$(image_label io.holycode.version.typescript)"
expected_tsx="$(image_label io.holycode.version.tsx)"
expected_pnpm="$(image_label io.holycode.version.pnpm)"
expected_netlify="$(image_label io.holycode.version.netlify-cli)"
expected_numpy="$(image_label io.holycode.version.numpy)"
expected_wrangler="$(image_label io.holycode.version.wrangler)"
expected_vercel="$(image_label io.holycode.version.vercel)"

secret_pattern='(_API_KEY|TOKEN|SECRET|PASSWORD)=[^[:space:]]+'

if docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$image" | grep -Ei "$secret_pattern"; then
  echo "image config contains non-empty secret-like environment variables" >&2
  exit 1
fi

if docker history --no-trunc "$image" | grep -Ei '(sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY)'; then
  echo "image history contains secret-like material" >&2
  exit 1
fi

docker run --rm --entrypoint sh \
  -e EXPECTED_OPENCODE="$expected_opencode" \
  -e EXPECTED_CLAUDE="$expected_claude" \
  -e EXPECTED_PAPERCLIP="$expected_paperclip" \
  -e EXPECTED_NPM="$expected_npm" \
  -e EXPECTED_TYPESCRIPT="$expected_typescript" \
  -e EXPECTED_TSX="$expected_tsx" \
  -e EXPECTED_PNPM="$expected_pnpm" \
  -e EXPECTED_NETLIFY="$expected_netlify" \
  -e EXPECTED_NUMPY="$expected_numpy" \
  -e EXPECTED_WRANGLER="$expected_wrangler" \
  -e EXPECTED_VERCEL="$expected_vercel" \
  "$image" -lc '
  set -eu

  node --version | grep -E "^v[0-9]+\\."
  npm --version | grep -Fx "$EXPECTED_NPM"
  opencode --version | grep -Fx "$EXPECTED_OPENCODE"

  test -f /usr/local/lib/node_modules/paperclipai/package.json
  test -f /usr/local/lib/node_modules/paperclipai/node_modules/@paperclipai/skills-catalog/generated/catalog.json
  node -e "console.log(require(\"/usr/local/lib/node_modules/paperclipai/package.json\").version)" | grep -Fx "$EXPECTED_PAPERCLIP"
  test -f /etc/s6-overlay/user-bundles.d/user/contents.d/opencode
  test -f /etc/s6-overlay/user-bundles.d/user/contents.d/xvfb
  test ! -e /etc/s6-overlay/s6-rc.d/user/contents.d/opencode

  grep -Fx "VERSION_ID=\"13\"" /etc/os-release
  python3 --version | grep -E "^Python 3\.13\."
  python3 -m pip --version
  python3 -m pip check
  python3 - <<PY
import importlib.metadata as metadata
print(metadata.version("hermes-agent"))
assert metadata.version("numpy") == "$EXPECTED_NUMPY"
assert metadata.version("requests") == "2.33.0"
assert metadata.version("Pillow") == "12.2.0"
assert metadata.version("rich") == "14.3.3"
PY

  command -v claude
  claude --version | grep -F "$EXPECTED_CLAUDE"

  pnpm --version | grep -Fx "$EXPECTED_PNPM"
  tsc --version | grep -Fx "Version $EXPECTED_TYPESCRIPT"
  tsx --version | grep -F "tsx v$EXPECTED_TSX"
  wrangler --version | grep -F "$EXPECTED_WRANGLER"
  vercel --version | grep -F "$EXPECTED_VERCEL"
  esbuild --version | grep -Fx "0.28.1"
  prisma --version >/dev/null
  node -e "const sharp=require(\"/usr/local/lib/node_modules/sharp-cli/node_modules/sharp\"); sharp({create:{width:1,height:1,channels:4,background:{r:0,g:0,b:0,alpha:1}}}).png().toBuffer().then(b=>{if(!b.length)process.exit(1)})"
  workerd_bin="$(find /usr/local/lib/node_modules/wrangler -path "*/workerd/bin/workerd" -type f -print -quit)"
  test -n "$workerd_bin"
  "$workerd_bin" --version >/dev/null
  netlify --version | grep -F "netlify-cli/$EXPECTED_NETLIFY"
  netlify build --help >/dev/null
  netlify deploy --help >/dev/null
  test -z "$(find /usr/local/lib/node_modules/netlify-cli -path "*/@netlify/local-functions-proxy-*/bin/local-functions-proxy" -print -quit)"
  chromium --version
  test -s /usr/local/share/holycode/dpkg-inventory.txt

  mkdir -p /tmp/wrangler-modern /tmp/wrangler-legacy
  printf "export default { fetch() { return new Response(\"ok\"); } };\n" > /tmp/wrangler-modern/worker.js
  cat > /tmp/wrangler-modern/wrangler.toml <<EOF
name = "holycode-wrangler"
main = "worker.js"
compatibility_date = "2026-07-15"

[env.staging]
name = "holycode-wrangler-staging"
EOF
  (cd /tmp/wrangler-modern && wrangler deploy --dry-run --env staging --outdir /tmp/wrangler-output >/tmp/wrangler-modern.log 2>&1)
  cp /tmp/wrangler-modern/worker.js /tmp/wrangler-legacy/worker.js
  cat > /tmp/wrangler-legacy/wrangler.toml <<EOF
name = "holycode-wrangler-legacy"
main = "worker.js"
compatibility_date = "2026-07-15"
legacy_env = true
EOF
  if (cd /tmp/wrangler-legacy && wrangler deploy --dry-run >/tmp/wrangler-legacy.log 2>&1); then
    echo "Wrangler unexpectedly accepted removed legacy_env configuration" >&2
    exit 1
  fi
  grep -F "legacy_env" /tmp/wrangler-legacy.log >/dev/null

  env | grep -E "(_API_KEY|TOKEN|SECRET|PASSWORD)=" | while read -r line; do
    case "$line" in
      *=) ;;
      *) echo "runtime contains non-empty secret-like environment variable: $line" >&2; exit 1 ;;
    esac
  done
'
