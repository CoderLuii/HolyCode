#!/usr/bin/env bash
set -euo pipefail

image="${1:?usage: scripts/smoke_image.sh <image>}"
seccomp_profile="${2:-config/chromium-seccomp.json}"

image_label() {
  docker inspect --format "{{ index .Config.Labels \"$1\" }}" "$image"
}

expected_opencode="$(image_label io.holycode.version.opencode)"
expected_claude="$(image_label io.holycode.version.claude-code)"
expected_paperclip="$(image_label io.holycode.version.paperclip)"
expected_claude_auth="$(image_label io.holycode.version.claude-auth-plugin)"
expected_npm="$(image_label io.holycode.version.npm)"
expected_npm_brace_expansion="$(image_label io.holycode.version.npm-brace-expansion)"
expected_npm_tar="$(image_label io.holycode.version.npm-tar)"
expected_pip_vendor_msgpack="$(image_label io.holycode.version.pip-vendor-msgpack)"
expected_pip_vendor_pkg_resources="$(image_label io.holycode.version.pip-vendor-pkg-resources)"
expected_typescript="$(image_label io.holycode.version.typescript)"
expected_tsx="$(image_label io.holycode.version.tsx)"
expected_pnpm="$(image_label io.holycode.version.pnpm)"
expected_numpy="$(image_label io.holycode.version.numpy)"
expected_wrangler="$(image_label io.holycode.version.wrangler)"
expected_vite="$(image_label io.holycode.version.vite)"
expected_prettier="$(image_label io.holycode.version.prettier)"
expected_prisma="$(image_label io.holycode.version.prisma)"
expected_lighthouse="$(image_label io.holycode.version.lighthouse)"
expected_s6="$(image_label io.holycode.version.s6-overlay)"
expected_fzf="$(image_label io.holycode.version.fzf)"
expected_github_cli="$(image_label io.holycode.version.github-cli)"

secret_pattern='(_API_KEY|TOKEN|SECRET|PASSWORD)=[^[:space:]]+'

if docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$image" | grep -Ei "$secret_pattern"; then
  echo "image config contains non-empty secret-like environment variables" >&2
  exit 1
fi

if docker history --no-trunc "$image" | grep -Ei '(sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH|EC) PRIVATE KEY)'; then
  echo "image history contains secret-like material" >&2
  exit 1
fi

docker run --rm --security-opt "seccomp=$seccomp_profile" --entrypoint sh \
  -e EXPECTED_OPENCODE="$expected_opencode" \
  -e EXPECTED_CLAUDE="$expected_claude" \
  -e EXPECTED_PAPERCLIP="$expected_paperclip" \
  -e EXPECTED_CLAUDE_AUTH="$expected_claude_auth" \
  -e EXPECTED_NPM="$expected_npm" \
  -e EXPECTED_NPM_BRACE_EXPANSION="$expected_npm_brace_expansion" \
  -e EXPECTED_NPM_TAR="$expected_npm_tar" \
  -e EXPECTED_PIP_VENDOR_MSGPACK="$expected_pip_vendor_msgpack" \
  -e EXPECTED_PIP_VENDOR_PKG_RESOURCES="$expected_pip_vendor_pkg_resources" \
  -e EXPECTED_TYPESCRIPT="$expected_typescript" \
  -e EXPECTED_TSX="$expected_tsx" \
  -e EXPECTED_PNPM="$expected_pnpm" \
  -e EXPECTED_NUMPY="$expected_numpy" \
  -e EXPECTED_WRANGLER="$expected_wrangler" \
  -e EXPECTED_VITE="$expected_vite" \
  -e EXPECTED_PRETTIER="$expected_prettier" \
  -e EXPECTED_PRISMA="$expected_prisma" \
  -e EXPECTED_LIGHTHOUSE="$expected_lighthouse" \
  -e EXPECTED_S6="$expected_s6" \
  -e EXPECTED_FZF="$expected_fzf" \
  -e EXPECTED_GITHUB_CLI="$expected_github_cli" \
  "$image" -lc '
  set -eu
  test ! -e /root/.npm
  export NPM_CONFIG_CACHE=/tmp/holycode-smoke-npm

  node --version | grep -E "^v[0-9]+\\."
  npm --version | grep -Fx "$EXPECTED_NPM"
  node -e "console.log(require(\"/usr/local/lib/node_modules/npm/node_modules/brace-expansion/package.json\").version)" | grep -Fx "$EXPECTED_NPM_BRACE_EXPANSION"
  (cd /usr/local/lib/node_modules/npm && npm ls brace-expansion --all >/dev/null)
  node -e "console.log(require(\"/usr/local/lib/node_modules/npm/node_modules/tar/package.json\").version)" | grep -Fx "$EXPECTED_NPM_TAR"
  (cd /usr/local/lib/node_modules/npm && npm ls tar --all >/dev/null)
  opencode --version | grep -Fx "$EXPECTED_OPENCODE"
  test -d "/package/admin/s6-overlay-$EXPECTED_S6"
  fzf --version | grep -E "^$EXPECTED_FZF([[:space:]]|$)"
  test "$(command -v gh)" = "/usr/local/bin/gh"
  gh --version | grep -F "gh version $EXPECTED_GITHUB_CLI"
  ! dpkg-query -W gh >/dev/null 2>&1

  test -f /usr/local/lib/node_modules/paperclipai/package.json
  test -f /usr/local/share/holycode/plugins/opencode-claude-auth/package.json
  test ! -e /root/.npm
  node -e "console.log(require(\"/usr/local/share/holycode/plugins/opencode-claude-auth/package.json\").version)" | grep -Fx "$EXPECTED_CLAUDE_AUTH"
  test -f /usr/local/lib/node_modules/paperclipai/node_modules/@paperclipai/skills-catalog/generated/catalog.json
  node -e "console.log(require(\"/usr/local/lib/node_modules/paperclipai/package.json\").version)" | grep -Fx "$EXPECTED_PAPERCLIP"
  (cd /usr/local/lib/node_modules/paperclipai && npm ls undici --all >/dev/null)
  node --input-type=module -e "const {testEnvironment}=await import(\"file:///usr/local/lib/node_modules/paperclipai/node_modules/@paperclipai/adapter-cursor-cloud/dist/server/index.js\"); const result=await testEnvironment({adapterType:\"cursor_cloud\",config:{}}); if(result.status!==\"fail\" || !result.checks.some((check)=>check.code===\"cursor_cloud_api_key_missing\")) process.exit(1)"
  test -f /etc/s6-overlay/user-bundles.d/user/contents.d/opencode
  test -f /etc/s6-overlay/user-bundles.d/user/contents.d/xvfb
  test ! -e /etc/s6-overlay/s6-rc.d/user/contents.d/opencode

  grep -Fx "VERSION_ID=\"13\"" /etc/os-release
  python3 --version | grep -E "^Python 3\.13\."
  python3 -m pip --version
  python3 -m pip check
  python3 -c "import pip._vendor.msgpack as msgpack; assert msgpack.__version__ == \"$EXPECTED_PIP_VENDOR_MSGPACK\"; import pip._vendor.pkg_resources"
  _PIP_USE_IMPORTLIB_METADATA=0 python3 -m pip list --format=json >/dev/null
  grep -Fx "msgpack==$EXPECTED_PIP_VENDOR_MSGPACK" /usr/local/lib/python3.13/dist-packages/pip/_vendor/vendor.txt
  grep -Fx "setuptools==$EXPECTED_PIP_VENDOR_PKG_RESOURCES" /usr/local/lib/python3.13/dist-packages/pip/_vendor/vendor.txt
  python3 -c "import json; components={item[\"name\"]:item[\"version\"] for item in json.load(open(\"/usr/local/lib/python3.13/dist-packages/pip/_vendor/bom.cdx.json\"))[\"components\"] if item.get(\"name\") in {\"msgpack\",\"setuptools\"}}; assert components[\"msgpack\"] == \"$EXPECTED_PIP_VENDOR_MSGPACK\"; assert components[\"setuptools\"] == \"$EXPECTED_PIP_VENDOR_PKG_RESOURCES\""
  psql --version | grep -F "psql (PostgreSQL) 17."
  ! dpkg-query -W postgresql-client >/dev/null 2>&1
  python3 - <<PY
import importlib.metadata as metadata
assert metadata.version("numpy") == "$EXPECTED_NUMPY"
assert metadata.version("requests") == "2.34.2"
assert metadata.version("Pillow") == "12.3.0"
assert metadata.version("pandas") == "3.0.5"
assert metadata.version("matplotlib") == "3.11.1"
assert metadata.version("tqdm") == "4.70.0"
assert metadata.version("fastapi") == "0.141.1"
assert metadata.version("uvicorn") == "0.52.1"
assert metadata.version("packaging") == "26.3"
assert metadata.version("wheel") == "0.47.0"
assert metadata.version("pip") == "26.2.1"
assert metadata.version("rich") == "15.0.0"
assert metadata.version("setuptools") == "84.0.0"
try:
    metadata.version("hermes-agent")
except metadata.PackageNotFoundError:
    pass
else:
    raise AssertionError("hermes-agent must not be bundled")
PY
  python3 -m venv /tmp/holycode-python-seed
  /tmp/holycode-python-seed/bin/python -m pip install --no-index \
    --find-links /usr/local/share/holycode/python-seed \
    pip==26.2.1 setuptools==84.0.0 packaging==26.3 wheel==0.47.0
  /tmp/holycode-python-seed/bin/python - <<PY
import importlib.metadata as metadata
assert metadata.version("pip") == "26.2.1"
assert metadata.version("setuptools") == "84.0.0"
assert metadata.version("packaging") == "26.3"
assert metadata.version("wheel") == "0.47.0"
PY

  command -v claude
  claude --version | grep -F "$EXPECTED_CLAUDE"
  if runuser -u opencode -- env \
    HOME=/home/opencode \
    USER=opencode \
    LOGNAME=opencode \
    XDG_CONFIG_HOME=/home/opencode/.config \
    XDG_CACHE_HOME=/home/opencode/.cache \
    XDG_DATA_HOME=/home/opencode/.local/share \
    XDG_STATE_HOME=/home/opencode/.local/state \
    claude auth status --json >/tmp/claude-auth-status.json; then
    echo "fresh image unexpectedly has an authenticated Claude session" >&2
    exit 1
  fi
  jq -e ".loggedIn == false and .authMethod == \"none\"" /tmp/claude-auth-status.json >/dev/null

  pnpm --version | grep -Fx "$EXPECTED_PNPM"
  tsc --version | grep -Fx "Version $EXPECTED_TYPESCRIPT"
  tsx --version | grep -F "tsx v$EXPECTED_TSX"
  wrangler --version | grep -F "$EXPECTED_WRANGLER"
  vite --version | grep -F "vite/$EXPECTED_VITE"
  prettier --version | grep -Fx "$EXPECTED_PRETTIER"
  prisma --version | grep -E "^prisma[[:space:]]+:[[:space:]]+$EXPECTED_PRISMA$"
  lighthouse --version | grep -Fx "$EXPECTED_LIGHTHOUSE"
  ! command -v vercel
  ! command -v sharp
  ! command -v concurrently
  ! command -v lhci
  ! command -v netlify
  ! command -v serve
  esbuild --version | grep -Fx "0.28.1"
  prisma --version >/dev/null
  workerd_bin="$(find /usr/local/lib/node_modules/wrangler -path "*/workerd/bin/workerd" -type f -print -quit)"
  test -n "$workerd_bin"
  "$workerd_bin" --version >/dev/null
  sharp_count=0
  while IFS= read -r package_json; do
    sharp_dir="${package_json%/package.json}"
    node -e "const sharp=require(process.argv[1]); sharp({create:{width:2,height:2,channels:4,background:{r:220,g:30,b:30,alpha:1}}}).png().toBuffer().then(buffer=>{if(buffer.length<10)process.exit(1)}).catch(error=>{console.error(error);process.exit(1)})" "$sharp_dir"
    sharp_count=$((sharp_count + 1))
  done <<EOF
$(find /usr/local/lib/node_modules -path "*/sharp/package.json" -type f | sort)
EOF
  test "$sharp_count" -gt 0
  grep -F "<policy domain=\"coder\" rights=\"none\" pattern=\"*\" />" /etc/ImageMagick-7/policy.xml >/dev/null
  grep -F "<policy domain=\"coder\" rights=\"read|write\" pattern=\"{GIF,JPEG,PNG,WEBP}\" />" /etc/ImageMagick-7/policy.xml >/dev/null
  chromium --version | grep -E "Chromium (15[1-9]|1[6-9][0-9]|[2-9][0-9]{2})\\."
  test "$(dpkg-query -W -f="\${Version}" chromium)" = "$(dpkg-query -W -f="\${Version}" chromium-sandbox)"
  test -u /usr/lib/chromium/chrome-sandbox
  runuser -u opencode -- chromium --headless --disable-gpu --disable-dev-shm-usage --dump-dom about:blank | grep -F "<html><head></head><body></body></html>"
  runuser -u opencode -- python3 -c "from playwright.sync_api import sync_playwright; from PIL import Image; p=sync_playwright().start(); b=p.chromium.launch(executable_path=\"/usr/bin/chromium\", args=[\"--disable-gpu\", \"--disable-dev-shm-usage\"]); page=b.new_page(viewport={\"width\": 320, \"height\": 200}); page.set_content(\"<main style=\\\"width:160px;height:100px;background:#d22\\\"></main>\"); page.screenshot(path=\"/tmp/holycode-chromium.png\"); b.close(); p.stop(); image=Image.open(\"/tmp/holycode-chromium.png\").convert(\"RGB\"); assert image.getbbox() and len(image.getcolors(maxcolors=1000000) or []) > 1"
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
