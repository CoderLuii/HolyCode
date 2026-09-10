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
expected_openspec="$(image_label io.holycode.version.openspec)"
expected_claude_auth="$(image_label io.holycode.version.claude-auth-plugin)"
expected_npm="$(image_label io.holycode.version.npm)"
expected_npm_brace_expansion="$(image_label io.holycode.version.npm-brace-expansion)"
expected_npm_tar="$(image_label io.holycode.version.npm-tar)"
expected_npm_ip_address="$(image_label io.holycode.version.npm-ip-address)"
expected_pm2_js_yaml="$(image_label io.holycode.version.pm2-js-yaml)"
expected_pip_vendor_msgpack="$(image_label io.holycode.version.pip-vendor-msgpack)"
expected_pip_vendor_pkg_resources="$(image_label io.holycode.version.pip-vendor-pkg-resources)"
expected_typescript="$(image_label io.holycode.version.typescript)"
expected_tsx="$(image_label io.holycode.version.tsx)"
expected_pnpm="$(image_label io.holycode.version.pnpm)"
expected_numpy="$(image_label io.holycode.version.numpy)"
expected_wrangler="$(image_label io.holycode.version.wrangler)"
expected_wrangler_miniflare="$(image_label io.holycode.version.wrangler-miniflare)"
expected_wrangler_sharp="$(image_label io.holycode.version.wrangler-sharp)"
expected_wrangler_sharp_libvips="$(image_label io.holycode.version.wrangler-sharp-libvips)"
expected_vite="$(image_label io.holycode.version.vite)"
expected_prettier="$(image_label io.holycode.version.prettier)"
expected_prisma="$(image_label io.holycode.version.prisma)"
expected_prisma_deepmerge="$(image_label io.holycode.version.prisma-deepmerge-ts)"
expected_prisma_mysql2="$(image_label io.holycode.version.prisma-mysql2)"
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
  -e EXPECTED_OPENSPEC="$expected_openspec" \
  -e EXPECTED_CLAUDE_AUTH="$expected_claude_auth" \
  -e EXPECTED_NPM="$expected_npm" \
  -e EXPECTED_NPM_BRACE_EXPANSION="$expected_npm_brace_expansion" \
  -e EXPECTED_NPM_TAR="$expected_npm_tar" \
  -e EXPECTED_NPM_IP_ADDRESS="$expected_npm_ip_address" \
  -e EXPECTED_PM2_JS_YAML="$expected_pm2_js_yaml" \
  -e EXPECTED_PIP_VENDOR_MSGPACK="$expected_pip_vendor_msgpack" \
  -e EXPECTED_PIP_VENDOR_PKG_RESOURCES="$expected_pip_vendor_pkg_resources" \
  -e EXPECTED_TYPESCRIPT="$expected_typescript" \
  -e EXPECTED_TSX="$expected_tsx" \
  -e EXPECTED_PNPM="$expected_pnpm" \
  -e EXPECTED_NUMPY="$expected_numpy" \
  -e EXPECTED_WRANGLER="$expected_wrangler" \
  -e EXPECTED_WRANGLER_MINIFLARE="$expected_wrangler_miniflare" \
  -e EXPECTED_WRANGLER_SHARP="$expected_wrangler_sharp" \
  -e EXPECTED_WRANGLER_SHARP_LIBVIPS="$expected_wrangler_sharp_libvips" \
  -e EXPECTED_VITE="$expected_vite" \
  -e EXPECTED_PRETTIER="$expected_prettier" \
  -e EXPECTED_PRISMA="$expected_prisma" \
  -e EXPECTED_PRISMA_DEEPMERGE="$expected_prisma_deepmerge" \
  -e EXPECTED_PRISMA_MYSQL2="$expected_prisma_mysql2" \
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
  node -e "console.log(require(\"/usr/local/lib/node_modules/npm/node_modules/ip-address/package.json\").version)" | grep -Fx "$EXPECTED_NPM_IP_ADDRESS"
  node -e "const pkg=require(\"/usr/local/lib/node_modules/npm/node_modules/socks/package.json\"); if(pkg.version!==\"2.8.9\" || pkg.dependencies[\"ip-address\"]!==\"^10.1.1\") process.exit(1)"
  (cd /usr/local/lib/node_modules/npm && npm ls ip-address --all >/dev/null)
  test "$(npm prefix -g)" = "/usr/local"
  node -e "console.log(require(\"/usr/local/lib/node_modules/pm2/node_modules/js-yaml/package.json\").version)" | grep -Fx "$EXPECTED_PM2_JS_YAML"
  node -e "const pkg=require(\"/usr/local/lib/node_modules/pm2/package.json\"); if(pkg.dependencies[\"js-yaml\"]!==process.env.EXPECTED_PM2_JS_YAML) process.exit(1)"
  (cd /usr/local/lib/node_modules/pm2 && npm ls js-yaml --all >/dev/null)
  node -e "const yaml=require(\"/usr/local/lib/node_modules/pm2/node_modules/js-yaml\"); const parsed=yaml.load(\"service:\\n  enabled: true\\n\"); if(parsed.service.enabled!==true) process.exit(1)"
  pm2_app=/tmp/holycode-smoke-pm2-app.js
  printf "setInterval(() => {}, 60000);\n" > "$pm2_app"
  PM2_HOME=/tmp/holycode-smoke-pm2 pm2 start "$pm2_app" --name holycode-smoke-pm2 --no-autorestart >/dev/null
  PM2_HOME=/tmp/holycode-smoke-pm2 pm2 --version | grep -Fx "7.0.4"
  PM2_HOME=/tmp/holycode-smoke-pm2 pm2 stop holycode-smoke-pm2 >/dev/null
  PM2_HOME=/tmp/holycode-smoke-pm2 pm2 kill >/dev/null
  rm -rf /tmp/holycode-smoke-pm2 "$pm2_app"
  opencode --version | grep -Fx "$EXPECTED_OPENCODE"
  test -d "/package/admin/s6-overlay-$EXPECTED_S6"
  fzf --version | grep -E "^$EXPECTED_FZF([[:space:]]|$)"
  test "$(command -v gh)" = "/usr/local/bin/gh"
  gh --version | grep -F "gh version $EXPECTED_GITHUB_CLI"
  ! dpkg-query -W gh >/dev/null 2>&1

  test -f /usr/local/lib/node_modules/paperclipai/package.json
  test -f /usr/local/share/holycode/plugins/opencode-claude-auth/package.json
  test -r /usr/local/share/holycode/THIRD-PARTY-NOTICES && test -s /usr/local/share/holycode/THIRD-PARTY-NOTICES
  test -r /usr/local/lib/node_modules/@anthropic-ai/claude-code/LICENSE.md && test -s /usr/local/lib/node_modules/@anthropic-ai/claude-code/LICENSE.md
  test -r /usr/local/lib/node_modules/pm2/GNU-AGPL-3.0.txt && test -s /usr/local/lib/node_modules/pm2/GNU-AGPL-3.0.txt
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
  pip --version | grep -F "pip 26.2.1"
  test "$(dpkg-query -W -f=\${db:Status-Status} python3-pip 2>/dev/null || true)" != installed
  test "$(dpkg-query -W -f=\${db:Status-Status} python3-setuptools 2>/dev/null || true)" != installed
  python3 -m pip check
  python3 -c "import pip._vendor.msgpack as msgpack; assert msgpack.__version__ == \"$EXPECTED_PIP_VENDOR_MSGPACK\"; assert msgpack.unpackb(msgpack.packb({\"holycode\": True})) == {\"holycode\": True}"
  python3 - <<PY
import pip._vendor.msgpack as msgpack
from pip._vendor.msgpack import fallback

payload = msgpack.packb({"holycode": True}) + b"\x00"
interleaved = bytearray(len(payload) * 2)
interleaved[::2] = payload
try:
    fallback.unpackb(memoryview(interleaved)[::2])
except msgpack.ExtraData as error:
    assert error.unpacked == {"holycode": True}
    assert error.extra == b"\x00"
else:
    raise AssertionError("ExtraData not raised")

try:
    fallback.unpackb(b"\xd9")
except ValueError:
    pass
else:
    raise AssertionError("truncated input accepted")

assert msgpack.Timestamp(0, 999999999).nanoseconds == 999999999
try:
    msgpack.Timestamp(0, 1000000000)
except ValueError:
    pass
else:
    raise AssertionError("invalid timestamp accepted")
PY
  grep -Fx "msgpack==$EXPECTED_PIP_VENDOR_MSGPACK" /usr/local/lib/python3.13/dist-packages/pip/_vendor/vendor.txt
  grep -Fx "setuptools==$EXPECTED_PIP_VENDOR_PKG_RESOURCES" /usr/local/lib/python3.13/dist-packages/pip/_vendor/vendor.txt
  python3 -c "import json; components={item[\"name\"]:item[\"version\"] for item in json.load(open(\"/usr/local/lib/python3.13/dist-packages/pip/_vendor/bom.cdx.json\"))[\"components\"] if item.get(\"name\")==\"msgpack\"}; assert components[\"msgpack\"] == \"$EXPECTED_PIP_VENDOR_MSGPACK\""
  python3 -c "import json; components={item[\"name\"]:item[\"version\"] for item in json.load(open(\"/usr/local/lib/python3.13/dist-packages/pip/_vendor/bom.cdx.json\"))[\"components\"] if item.get(\"name\")==\"setuptools\"}; assert components[\"setuptools\"] == \"$EXPECTED_PIP_VENDOR_PKG_RESOURCES\""
  python3 -c "import pip._vendor.pkg_resources"
  _PIP_USE_IMPORTLIB_METADATA=0 python3 -m pip list --format=json >/dev/null
  psql --version | grep -F "psql (PostgreSQL) 17."
  ! dpkg-query -W postgresql-client >/dev/null 2>&1
  python3 - <<PY
import importlib.metadata as metadata
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
from fontTools.ttLib import TTFont
from matplotlib import pyplot as plt
from matplotlib.font_manager import findfont
import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient
from lxml import etree
from pydantic import BaseModel

assert metadata.version("numpy") == "$EXPECTED_NUMPY"
assert metadata.version("requests") == "2.34.2"
assert metadata.version("Pillow") == "12.3.0"
assert metadata.version("pandas") == "3.0.5"
assert metadata.version("matplotlib") == "3.11.1"
assert metadata.version("fonttools") == "4.65.0"
assert metadata.version("tqdm") == "4.70.0"
assert metadata.version("fastapi") == "0.141.1"
assert metadata.version("uvicorn") == "0.52.4"
assert metadata.version("packaging") == "26.3"
assert metadata.version("wheel") == "0.48.0"
assert metadata.version("pip") == "26.2.1"
assert metadata.version("rich") == "15.0.0"
assert metadata.version("setuptools") == "84.0.0"
try:
    metadata.version("hermes-agent")
except metadata.PackageNotFoundError:
    pass
else:
    raise AssertionError("hermes-agent must not be bundled")

assert np.array([1, 2, 3]).sum() == 6
assert pd.Series([1, 2, 3]).mean() == 2
assert etree.fromstring(b"<root><value>holycode</value></root>").findtext("value") == "holycode"

font_path = findfont("DejaVu Sans", fallback_to_default=False)
with TTFont(font_path) as font:
    assert "name" in font
rendered = BytesIO()
figure, axis = plt.subplots(figsize=(2, 1))
axis.text(0.5, 0.5, "HolyCode", ha="center", va="center")
figure.savefig(rendered, format="png")
plt.close(figure)
assert rendered.getvalue().startswith(b"\x89PNG\r\n\x1a\n")

class Health(BaseModel):
    status: str

app = FastAPI()

@app.get("/health", response_model=Health)
def health():
    return {"status": "ok"}

response = TestClient(app).get("/health")
assert response.status_code == 200
assert response.json() == {"status": "ok"}
PY
  python3 -m venv /tmp/holycode-python-seed
  /tmp/holycode-python-seed/bin/python -m pip install --no-index \
    --find-links /usr/local/share/holycode/python-seed \
    pip==26.2.1 setuptools==84.0.0 packaging==26.3 wheel==0.48.0
  /tmp/holycode-python-seed/bin/python - <<PY
import importlib.metadata as metadata
assert metadata.version("pip") == "26.2.1"
assert metadata.version("setuptools") == "84.0.0"
assert metadata.version("packaging") == "26.3"
assert metadata.version("wheel") == "0.48.0"
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
  command -v tsserver
  typescript_workspace="$(mktemp -d)"
  printf "const value: string = \047holycode\047;\n" > "$typescript_workspace/index.ts"
  tsc --strict --noEmit "$typescript_workspace/index.ts"
  node - "$typescript_workspace/index.ts" <<NODE
const ts = require("/usr/local/lib/node_modules/typescript/lib/typescript.js");
const program = ts.createProgram([process.argv[2]], { strict: true, noEmit: true });
const diagnostics = ts.getPreEmitDiagnostics(program);
if (diagnostics.length !== 0 || ts.version !== process.env.EXPECTED_TYPESCRIPT) process.exit(1);
NODE
  rm -rf "$typescript_workspace"

  pnpm_workspace="$(mktemp -d)"
  mkdir -p "$pnpm_workspace/dependency" "$pnpm_workspace/project"
  cat > "$pnpm_workspace/dependency/package.json" <<EOF
{"name":"holycode-local-fixture","version":"1.0.0","main":"index.cjs"}
EOF
  printf "module.exports = \"holycode\";\n" > "$pnpm_workspace/dependency/index.cjs"
  (cd "$pnpm_workspace/dependency" && pnpm pack --pack-destination "$pnpm_workspace" >/dev/null)
  cat > "$pnpm_workspace/project/package.json" <<EOF
{"name":"holycode-offline-project","private":true,"scripts":{"verify":"node verify.cjs"},"dependencies":{"holycode-local-fixture":"file:../holycode-local-fixture-1.0.0.tgz"}}
EOF
  printf "if (require(\"holycode-local-fixture\") !== \"holycode\") process.exit(1);\n" > "$pnpm_workspace/project/verify.cjs"
  (cd "$pnpm_workspace/project" && pnpm install --offline --ignore-scripts)
  test -f "$pnpm_workspace/project/pnpm-lock.yaml"
  (cd "$pnpm_workspace/project" && pnpm run verify)
  rm -rf "$pnpm_workspace"

  tsx --version | grep -F "tsx v$EXPECTED_TSX"
  wrangler --version | grep -F "$EXPECTED_WRANGLER"
  wrangler_package=/usr/local/lib/node_modules/wrangler/package.json
  wrangler_node_modules=/usr/local/lib/node_modules/wrangler/node_modules
  wrangler_miniflare_package=/usr/local/lib/node_modules/wrangler/node_modules/miniflare/package.json
  wrangler_sharp_dir=/usr/local/lib/node_modules/wrangler/node_modules/sharp
  node -e "const pkg=require(process.argv[1]); if(pkg.version!==process.env.EXPECTED_WRANGLER || pkg.dependencies.miniflare!==process.env.EXPECTED_WRANGLER_MINIFLARE) process.exit(1)" "$wrangler_package"
  node -e "const pkg=require(process.argv[1]); if(pkg.version!==process.env.EXPECTED_WRANGLER_MINIFLARE || pkg.dependencies.sharp!==process.env.EXPECTED_WRANGLER_SHARP) process.exit(1)" "$wrangler_miniflare_package"
  node -e "const pkg=require(process.argv[1]); if(pkg.version!==process.env.EXPECTED_WRANGLER_SHARP) process.exit(1)" "$wrangler_sharp_dir/package.json"
  case "$(uname -m)" in
    x86_64) wrangler_sharp_arch=x64 ;;
    aarch64|arm64) wrangler_sharp_arch=arm64 ;;
    *) echo "unsupported Sharp runtime architecture: $(uname -m)" >&2; exit 1 ;;
  esac
  wrangler_sharp_native_package="@img/sharp-linux-$wrangler_sharp_arch"
  wrangler_sharp_libvips_package="@img/sharp-libvips-linux-$wrangler_sharp_arch"
  wrangler_sharp_native_dir="$wrangler_node_modules/@img/sharp-linux-$wrangler_sharp_arch"
  wrangler_sharp_libvips_dir="$wrangler_node_modules/@img/sharp-libvips-linux-$wrangler_sharp_arch"
  node -e "const pkg=require(process.argv[1]); if(pkg.version!==process.env.EXPECTED_WRANGLER_SHARP || pkg.optionalDependencies[process.argv[2]]!==process.env.EXPECTED_WRANGLER_SHARP_LIBVIPS) process.exit(1)" "$wrangler_sharp_native_dir/package.json" "$wrangler_sharp_libvips_package"
  node -e "const pkg=require(process.argv[1]); if(pkg.version!==process.env.EXPECTED_WRANGLER_SHARP_LIBVIPS) process.exit(1)" "$wrangler_sharp_libvips_dir/package.json"
  test "$(find /usr/local/lib/node_modules/wrangler -path "*/sharp/package.json" -type f | wc -l)" -eq 1
  test "$(find /usr/local/lib/node_modules/wrangler -path "*/$wrangler_sharp_native_package/package.json" -type f | wc -l)" -eq 1
  test "$(find /usr/local/lib/node_modules/wrangler -path "*/$wrangler_sharp_libvips_package/package.json" -type f | wc -l)" -eq 1
  (cd /usr/local/lib/node_modules/wrangler && npm ls sharp --all >/dev/null)
  node -e "const sharp=require(process.argv[1]); if(sharp.versions.sharp!==process.env.EXPECTED_WRANGLER_SHARP || sharp.versions.heif!==\"1.23.2\") process.exit(1); sharp({create:{width:2,height:2,channels:4,background:{r:220,g:30,b:30,alpha:1}}}).avif().toBuffer().then(buffer=>sharp(buffer).raw().toBuffer({resolveWithObject:true})).then(({data,info})=>{if(info.width!==2 || info.height!==2 || info.channels!==4 || data.length!==16) process.exit(1)}).catch(error=>{console.error(error);process.exit(1)})" "$wrangler_sharp_dir"
  vite --version | grep -F "vite/$EXPECTED_VITE"
  vite_workspace="$(mktemp -d)"
  printf "<main>HolyCode Vite smoke</main>\n" > "$vite_workspace/index.html"
  vite build "$vite_workspace" >/tmp/holycode-vite-build.log 2>&1
  test -s "$vite_workspace/dist/index.html"
  vite_port=4173
  vite preview "$vite_workspace" --host 127.0.0.1 --port "$vite_port" --strictPort \
    >/tmp/holycode-vite-preview.log 2>&1 &
  vite_pid=$!
  vite_ready=false
  for attempt in 1 2 3 4 5; do
    if curl -fsS "http://127.0.0.1:$vite_port/" >/tmp/holycode-vite-response.html; then
      vite_ready=true
      break
    fi
    sleep 1
  done
  test "$vite_ready" = true
  grep -F "HolyCode Vite smoke" /tmp/holycode-vite-response.html >/dev/null
  kill "$vite_pid"
  wait "$vite_pid" || true
  rm -rf "$vite_workspace" /tmp/holycode-vite-build.log \
    /tmp/holycode-vite-preview.log /tmp/holycode-vite-response.html
  prettier --version | grep -Fx "$EXPECTED_PRETTIER"
  prisma --version | grep -E "^prisma[[:space:]]+:[[:space:]]+$EXPECTED_PRISMA$"
  node -e "console.log(require(\"/usr/local/lib/node_modules/prisma/node_modules/deepmerge-ts/package.json\").version)" | grep -Fx "$EXPECTED_PRISMA_DEEPMERGE"
  node -e "const pkg=require(\"/usr/local/lib/node_modules/prisma/node_modules/@prisma/config/package.json\"); if(pkg.dependencies[\"deepmerge-ts\"]!==process.env.EXPECTED_PRISMA_DEEPMERGE) process.exit(1)"
  (cd /usr/local/lib/node_modules/prisma && npm ls deepmerge-ts --all >/dev/null)
  node -e "console.log(require(\"/usr/local/lib/node_modules/prisma/node_modules/mysql2/package.json\").version)" | grep -Fx "$EXPECTED_PRISMA_MYSQL2"
  node -e "const pkg=require(\"/usr/local/lib/node_modules/prisma/package.json\"); if(pkg.dependencies.mysql2!==process.env.EXPECTED_PRISMA_MYSQL2) process.exit(1)"
  (cd /usr/local/lib/node_modules/prisma && npm ls mysql2 --all >/dev/null)
  node -e "const mysql=require(\"/usr/local/lib/node_modules/prisma/node_modules/mysql2\"); if(typeof mysql.createConnection!==\"function\") process.exit(1)"
  lighthouse --version | grep -Fx "$EXPECTED_LIGHTHOUSE"
  ! command -v vercel
  ! command -v sharp
  ! command -v concurrently
  ! command -v lhci
  ! command -v netlify
  ! command -v serve
  esbuild --version | grep -Fx "0.28.2"
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

docker run --rm --network none --read-only \
  --tmpfs /tmp:rw,exec,nosuid,nodev,mode=1777,size=64m \
  --cap-drop ALL --security-opt no-new-privileges \
  --user 1000:1000 --workdir /tmp --entrypoint sh \
  "$image" -c '
  set -eu
  export HOME=/tmp/cc-home
  export CLAUDE_CONFIG_DIR=/tmp/cc-config
  export NO_COLOR=1
  test -z "${ANTHROPIC_API_KEY:-}"
  mkdir -p "$HOME" "$CLAUDE_CONFIG_DIR" /tmp/fixture/traversal/.claude-plugin
  cat > /tmp/fixture/traversal/.claude-plugin/marketplace.json <<EOF
{"name":"traversal-fixture","owner":{"name":"fixture"},"plugins":[{"name":"escape-plugin","source":"../outside"}]}
EOF
  if claude plugin validate /tmp/fixture/traversal --json >/tmp/traversal-validation.json 2>&1; then
    echo "Claude unexpectedly accepted a marketplace source outside its root" >&2
    exit 1
  fi
  grep -F "Path contains" /tmp/traversal-validation.json >/dev/null

  plugin_dir=/tmp/fixture/market/plugins/escape-plugin
  mkdir -p /tmp/fixture/market/.claude-plugin "$plugin_dir/.claude-plugin" \
    "$plugin_dir/skills/safe" /tmp/fixture/outside/leak
  cat > /tmp/fixture/market/.claude-plugin/marketplace.json <<EOF
{"name":"containment-fixture","owner":{"name":"fixture"},"plugins":[{"name":"escape-plugin","source":"./plugins/escape-plugin","version":"1.0.0"}]}
EOF
  cat > "$plugin_dir/.claude-plugin/plugin.json" <<EOF
{"name":"escape-plugin","version":"1.0.0","description":"HolyCode marketplace containment fixture"}
EOF
  cat > "$plugin_dir/skills/safe/SKILL.md" <<EOF
---
name: safe
description: Safe HolyCode containment fixture
---

SAFE_MARKER_2_1_268
EOF
  printf "OUTSIDE_MARKER_2_1_268\n" > /tmp/fixture/outside/leak/secret.txt
  ln -s /tmp/fixture/outside/leak "$plugin_dir/leak-dir"
  test "$(readlink -f "$plugin_dir/leak-dir")" = /tmp/fixture/outside/leak

  claude plugin marketplace add /tmp/fixture/market
  claude plugin install escape-plugin@containment-fixture --scope user
  claude_plugin_cache="$CLAUDE_CONFIG_DIR/plugins/cache/containment-fixture/escape-plugin/1.0.0"
  test -f "$claude_plugin_cache/skills/safe/SKILL.md"
  grep -F "SAFE_MARKER_2_1_268" "$claude_plugin_cache/skills/safe/SKILL.md" >/dev/null
  test ! -e "$claude_plugin_cache/leak-dir"
  test ! -L "$claude_plugin_cache/leak-dir"
  if grep -R -F "OUTSIDE_MARKER_2_1_268" "$claude_plugin_cache"; then
    echo "Claude copied a symlink target outside the marketplace root" >&2
    exit 1
  fi
'

openspec_workspace="$(mktemp -d)"
cleanup_openspec_workspace() {
  docker run --rm --network none --user 0:0 --entrypoint sh \
    -v "$openspec_workspace:/workspace" \
    "$image" -c 'find /workspace -mindepth 1 -delete' >/dev/null 2>&1 || true
  rm -rf "$openspec_workspace"
}
trap cleanup_openspec_workspace EXIT
chmod 0777 "$openspec_workspace"
docker run --rm --network none --user 1000:1000 --entrypoint sh \
  -e EXPECTED_OPENSPEC="$expected_openspec" \
  -e OPENSPEC_TELEMETRY=0 \
  -v "$openspec_workspace:/workspace" \
  -w /workspace \
  "$image" -lc '
  set -eu
  test "$(openspec --version)" = "$EXPECTED_OPENSPEC"
  npm ls -g --depth=0 "@fission-ai/openspec@$EXPECTED_OPENSPEC"
  openspec init --tools opencode
  test -d openspec
  openspec list --json >/tmp/openspec-list.json
  snapshot_openspec_workspace() {
    {
      find . -xdev -printf "%P|%y|%m|%U:%G\n" | LC_ALL=C sort
      find . -xdev -type l -printf "%P|%l\n" | LC_ALL=C sort
      find . -xdev -type f -print0 | LC_ALL=C sort -z | xargs -0r sha256sum
    } | sha256sum
  }
  openspec_snapshot_before="$(snapshot_openspec_workspace)"
  openspec init --tools opencode
  test -d openspec
  openspec_snapshot_after="$(snapshot_openspec_workspace)"
  test "$openspec_snapshot_before" = "$openspec_snapshot_after"
  openspec new change holycode-smoke
  mkdir -p openspec/changes/holycode-smoke/specs/holycode-smoke
  printf "%s\n" \
    "## Why" "" "Exercise the OpenSpec apply and archive lifecycle offline." "" \
    "## What Changes" "" "- Add a disposable HolyCode smoke capability." "" \
    "## Capabilities" "" "### New Capabilities" \
    "- holycode-smoke: Verifies the bundled OpenSpec lifecycle." "" \
    "### Modified Capabilities" "" "## Impact" "" \
    "Only the disposable smoke workspace is affected." \
    > openspec/changes/holycode-smoke/proposal.md
  printf "%s\n" \
    "## Purpose" "" \
    "Verifies that HolyCode can complete and archive an OpenSpec change without network access." "" \
    "## ADDED Requirements" "" "### Requirement: Offline lifecycle" \
    "The fixture SHALL complete the OpenSpec apply and archive lifecycle offline." "" \
    "#### Scenario: Archive completed change" \
    "- **WHEN** the disposable task is marked complete" \
    "- **THEN** OpenSpec archives the change into the canonical specification tree" \
    > openspec/changes/holycode-smoke/specs/holycode-smoke/spec.md
  printf "%s\n" \
    "## Context" "" "The smoke fixture runs with Docker networking disabled." "" \
    "## Goals / Non-Goals" "" "**Goals:**" \
    "Prove local apply guidance and archive behavior." "" "**Non-Goals:**" \
    "No product project files are changed." "" "## Decisions" "" \
    "Use one disposable capability and one completed task." "" \
    "## Risks / Trade-offs" "" \
    "The fixture checks the bundled CLI workflow, not an external integration." \
    > openspec/changes/holycode-smoke/design.md
  printf "%s\n" "## 1. Lifecycle" "" \
    "- [ ] 1.1 Complete the disposable fixture and verify strict validation passes" \
    > openspec/changes/holycode-smoke/tasks.md
  openspec validate holycode-smoke --strict
  openspec instructions apply --change holycode-smoke --json >/tmp/openspec-apply.json
  jq -e ".state == \"ready\"" /tmp/openspec-apply.json >/dev/null
  sed -i "s/- \[ \]/- [x]/" openspec/changes/holycode-smoke/tasks.md
  openspec archive holycode-smoke --yes --json >/tmp/openspec-archive.json
  test -s openspec/specs/holycode-smoke/spec.md
  test -d openspec/changes/archive/
  find openspec/changes/archive/ -path "*-holycode-smoke/tasks.md" -type f -print -quit | grep -q .
'
