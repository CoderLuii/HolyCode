# ==============================================================================
# HolyCode - Pre-configured Docker Environment for OpenCode
# https://github.com/coderluii/holycode
# ==============================================================================

# renovate: datasource=github-releases depName=cli/cli
ARG GITHUB_CLI_VERSION=2.103.3
# renovate: datasource=github-releases depName=junegunn/fzf
ARG FZF_VERSION=0.74.5
# renovate: datasource=github-releases depName=jesseduffield/lazygit
ARG LAZYGIT_VERSION=0.66.2

FROM node:24.22.2-trixie-slim@sha256:54f84b4cf8432b21aaffd5d3ce8d41e12cea0d10d33c09d2f3c9879d49d6b446

# ---------- Build args ----------
ARG GITHUB_CLI_VERSION
ARG FZF_VERSION
ARG LAZYGIT_VERSION
# renovate: datasource=github-releases depName=just-containers/s6-overlay
ARG S6_OVERLAY_VERSION=3.2.3.2
# renovate: datasource=github-releases depName=dandavison/delta
ARG DELTA_VERSION=0.20.1
# renovate: datasource=github-releases depName=eza-community/eza
ARG EZA_VERSION=0.23.5
# renovate: datasource=npm depName=opencode-ai
ARG OPENCODE_VERSION=1.19.5
# renovate: datasource=npm depName=@anthropic-ai/claude-code
ARG CLAUDE_CODE_VERSION=2.1.318
# renovate: datasource=npm depName=paperclipai
ARG PAPERCLIP_VERSION=2026.831.1
# renovate: datasource=npm depName=@cursor/sdk
ARG PAPERCLIP_CURSOR_SDK_VERSION=1.3.1
# renovate: datasource=npm depName=jsdom
ARG PAPERCLIP_JSDOM_VERSION=30.1.3
# renovate: datasource=npm depName=@fission-ai/openspec
ARG OPENSPEC_VERSION=1.14.3
# renovate: datasource=npm depName=undici
ARG PAPERCLIP_UNDICI_VERSION=8.12.3
# renovate: datasource=npm depName=opencode-claude-auth
ARG CLAUDE_AUTH_PLUGIN_VERSION=2.2.1
# renovate: datasource=npm depName=typescript
ARG TYPESCRIPT_VERSION=6.0.3
# renovate: datasource=npm depName=npm
ARG NPM_VERSION=12.2.2
# renovate: datasource=npm depName=node-gyp
ARG NPM_NODE_GYP_VERSION=13.0.0
# renovate: datasource=npm depName=undici
ARG NPM_NODE_GYP_UNDICI_VERSION=6.29.1
# renovate: datasource=npm depName=js-yaml
ARG PM2_JS_YAML_VERSION=4.3.2
# renovate: datasource=npm depName=tsx
ARG TSX_VERSION=4.23.15
# renovate: datasource=npm depName=pnpm
ARG PNPM_VERSION=12.16.1
# renovate: datasource=npm depName=vite
ARG VITE_VERSION=8.3.5
# renovate: datasource=npm depName=prettier
ARG PRETTIER_VERSION=3.9.10
# renovate: datasource=npm depName=prisma
ARG PRISMA_VERSION=7.10.1
# renovate: datasource=npm depName=deepmerge-ts
ARG PRISMA_DEEPMERGE_VERSION=8.0.2
# renovate: datasource=npm depName=mysql2
ARG PRISMA_MYSQL2_VERSION=3.24.4
# renovate: datasource=npm depName=lighthouse
ARG LIGHTHOUSE_VERSION=13.6.0
# renovate: datasource=npm depName=wrangler
ARG WRANGLER_VERSION=4.157.0
# renovate: datasource=npm depName=miniflare
ARG WRANGLER_MINIFLARE_VERSION=5.20261103.0-beta
# renovate: datasource=npm depName=sharp
ARG WRANGLER_SHARP_VERSION=0.35.5
# renovate: datasource=npm depName=@img/sharp-libvips-linux-x64
ARG WRANGLER_SHARP_LIBVIPS_VERSION=1.3.4
# renovate: datasource=npm depName=eslint
ARG ESLINT_VERSION=10.13.0
# renovate: datasource=pypi depName=numpy
ARG NUMPY_VERSION=2.5.4
# renovate: datasource=pypi depName=pip
ARG PIP_VERSION=26.3
ARG PIP_VENDOR_MSGPACK_VERSION=1.2.4
ARG PIP_VENDOR_PKG_RESOURCES_VERSION=70.3.0
ARG PIP_VENDOR_URLLIB3_VERSION=2.8.0
# renovate: datasource=pypi depName=setuptools
ARG SETUPTOOLS_VERSION=84.2.1
ARG RELEASE_APT_REFRESH=2026-11-04
ARG RELEASE_VERSION=v1.2.9
ARG TARGETARCH

LABEL org.opencontainers.image.source=https://github.com/CoderLuii/HolyCode \
    io.holycode.release=${RELEASE_VERSION} \
    io.holycode.version.github-cli=${GITHUB_CLI_VERSION} \
    io.holycode.version.opencode=${OPENCODE_VERSION} \
    io.holycode.version.claude-code=${CLAUDE_CODE_VERSION} \
    io.holycode.version.paperclip=${PAPERCLIP_VERSION} \
    io.holycode.version.paperclip-cursor-sdk=${PAPERCLIP_CURSOR_SDK_VERSION} \
    io.holycode.version.paperclip-jsdom=${PAPERCLIP_JSDOM_VERSION} \
    io.holycode.version.paperclip-undici=${PAPERCLIP_UNDICI_VERSION} \
    io.holycode.version.openspec=${OPENSPEC_VERSION} \
    io.holycode.version.claude-auth-plugin=${CLAUDE_AUTH_PLUGIN_VERSION} \
    io.holycode.version.npm=${NPM_VERSION} \
    io.holycode.version.npm-node-gyp=${NPM_NODE_GYP_VERSION} \
    io.holycode.version.npm-node-gyp-undici=${NPM_NODE_GYP_UNDICI_VERSION} \
    io.holycode.version.pm2-js-yaml=${PM2_JS_YAML_VERSION} \
    io.holycode.version.pip-vendor-msgpack=${PIP_VENDOR_MSGPACK_VERSION} \
    io.holycode.version.pip-vendor-pkg-resources=${PIP_VENDOR_PKG_RESOURCES_VERSION} \
    io.holycode.version.pip-vendor-urllib3=${PIP_VENDOR_URLLIB3_VERSION} \
    io.holycode.version.typescript=${TYPESCRIPT_VERSION} \
    io.holycode.version.tsx=${TSX_VERSION} \
    io.holycode.version.pnpm=${PNPM_VERSION} \
    io.holycode.version.vite=${VITE_VERSION} \
    io.holycode.version.prettier=${PRETTIER_VERSION} \
    io.holycode.version.prisma=${PRISMA_VERSION} \
    io.holycode.version.prisma-deepmerge-ts=${PRISMA_DEEPMERGE_VERSION} \
    io.holycode.version.prisma-mysql2=${PRISMA_MYSQL2_VERSION} \
    io.holycode.version.lighthouse=${LIGHTHOUSE_VERSION} \
    io.holycode.version.s6-overlay=${S6_OVERLAY_VERSION} \
    io.holycode.version.fzf=${FZF_VERSION} \
    io.holycode.version.lazygit=${LAZYGIT_VERSION} \
    io.holycode.version.delta=${DELTA_VERSION} \
    io.holycode.version.wrangler=${WRANGLER_VERSION} \
    io.holycode.version.wrangler-miniflare=${WRANGLER_MINIFLARE_VERSION} \
    io.holycode.version.wrangler-sharp=${WRANGLER_SHARP_VERSION} \
    io.holycode.version.wrangler-sharp-libvips=${WRANGLER_SHARP_LIBVIPS_VERSION} \
    io.holycode.version.numpy=${NUMPY_VERSION}

# ---------- Environment ----------
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    DISPLAY=:99 \
    DBUS_SESSION_BUS_ADDRESS=disabled: \
    CHROME_PATH=/usr/bin/chromium \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium \
    CHROMIUM_FLAGS="--disable-gpu --disable-dev-shm-usage" \
    OPENCODE_DISABLE_AUTOUPDATE=true \
    OPENCODE_DISABLE_TERMINAL_TITLE=true
ENV OPENSPEC_TELEMETRY=0

# ---------- s6-overlay v3 (multi-arch) ----------
RUN test -n "${RELEASE_APT_REFRESH}" && apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends xz-utils curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*
RUN S6_ARCH=$(case "$TARGETARCH" in arm64) echo "aarch64";; *) echo "x86_64";; esac) && \
    S6_ARCH_SHA256=$(case "$TARGETARCH" in \
      arm64) echo "b17f17a82e7a515c682a91edaf2ffdabb73f891981b6c1fd712115693a2f8b4c";; \
      *) echo "e6befcc96a437a3831386ecfc51808c5d3e939dc5fe3c02ae9284599e8aa2408";; \
    esac) && \
    curl --disable --retry 8 --retry-all-errors --retry-max-time 300 --remove-on-error --connect-timeout 15 --max-time 300 -fsSL -o /tmp/s6-overlay-noarch.tar.xz \
      "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz" && \
    curl --disable --retry 8 --retry-all-errors --retry-max-time 300 --remove-on-error --connect-timeout 15 --max-time 300 -fsSL -o /tmp/s6-overlay-arch.tar.xz \
      "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${S6_ARCH}.tar.xz" && \
    echo "5379750ed30a84bbd2e2dd74847ba6b5bd29cd0b2e3ea2ec58049b57eb2eda12  /tmp/s6-overlay-noarch.tar.xz" | sha256sum -c - && \
    echo "${S6_ARCH_SHA256}  /tmp/s6-overlay-arch.tar.xz" | sha256sum -c - && \
    tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz && \
    tar -C / -Jxpf /tmp/s6-overlay-arch.tar.xz && \
    rm /tmp/s6-overlay-*.tar.xz

# ---------- Locale configuration ----------
RUN apt-get update && apt-get install -y --no-install-recommends locales sudo && rm -rf /var/lib/apt/lists/* && \
    sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

# ---------- Rename node user to opencode ----------
# The Node slim base already has UID 1000 as 'node', rename it to 'opencode'
RUN usermod -l opencode -d /home/opencode -m node && \
    groupmod -n opencode node && \
    echo "opencode ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/opencode && \
    chmod 0440 /etc/sudoers.d/opencode

# ==============================================================================
# TOOL SECTIONS - Edit these to customize your image
# ==============================================================================

# ---------- Core tools ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Shell essentials
    git curl wget jq unzip zip tar tree less vim \
    # Search and navigation
    ripgrep fd-find bat bubblewrap \
    # Process and network
    htop procps iproute2 lsof strace \
    # Build essentials (needed for native npm addons)
    build-essential pkg-config \
    postgresql-client-17 redis-tools sqlite3 \
    # SSH client (NOT server)
    openssh-client \
    imagemagick \
    fonts-inter \
    tmux \
    && rm -rf /var/lib/apt/lists/*

RUN chmod u+s /usr/bin/bwrap

# ---------- bat symlink (Debian names it batcat) ----------
RUN ln -sf /usr/bin/batcat /usr/local/bin/bat 2>/dev/null || true

# ---------- fzf ----------
RUN FZF_SHA256=$(case "$TARGETARCH" in \
      arm64) echo "cf058001da21724a469b714a29cf4aab9cbe860d218a0d6c1b5b661efad7784c";; \
      *) echo "d47d7f882972c7d674dbbba998ffa4116e68379616ffac7695d0671e9a722c5f";; \
    esac) && \
    curl --disable --retry 8 --retry-all-errors --retry-max-time 300 --remove-on-error --connect-timeout 15 --max-time 300 -fsSL -o /tmp/fzf.tar.gz \
      "https://github.com/junegunn/fzf/releases/download/v${FZF_VERSION}/fzf-${FZF_VERSION}-linux_${TARGETARCH}.tar.gz" && \
    echo "${FZF_SHA256}  /tmp/fzf.tar.gz" | sha256sum -c - && \
    tar -C /tmp -xzf /tmp/fzf.tar.gz fzf && \
    install -m 0755 /tmp/fzf /usr/local/bin/fzf && \
    rm /tmp/fzf /tmp/fzf.tar.gz && \
    fzf --version | grep -F "${FZF_VERSION}"

# ---------- Python 3 (for user projects) ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
    pandoc ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# ---------- GitHub CLI ----------
RUN GH_SHA256=$(case "$TARGETARCH" in \
      arm64) echo "ee32df2323c8847f5fac6cb6b4b69ca75828e9329a8f22f677021f7b3306ce63";; \
      *) echo "4c806978ffce1cec70853302a56d70ac6da4f19bae7adca4e1a8ab00633dd91d";; \
    esac) && \
    curl --disable --retry 8 --retry-all-errors --retry-max-time 300 --remove-on-error --connect-timeout 15 --max-time 300 -fsSL -o /tmp/gh.tar.gz \
      "https://github.com/cli/cli/releases/download/v${GITHUB_CLI_VERSION}/gh_${GITHUB_CLI_VERSION}_linux_${TARGETARCH}.tar.gz" && \
    echo "${GH_SHA256}  /tmp/gh.tar.gz" | sha256sum -c - && \
    tar -C /tmp -xzf /tmp/gh.tar.gz && \
    install -m 0755 "/tmp/gh_${GITHUB_CLI_VERSION}_linux_${TARGETARCH}/bin/gh" /usr/local/bin/gh && \
    rm -rf /tmp/gh.tar.gz "/tmp/gh_${GITHUB_CLI_VERSION}_linux_${TARGETARCH}" && \
    gh --version | grep -F "gh version ${GITHUB_CLI_VERSION}"

# ---------- lazygit ----------
RUN LAZYGIT_ARCH=$(case "$TARGETARCH" in arm64) echo "arm64";; *) echo "x86_64";; esac) && \
    LAZYGIT_SHA256=$(case "$TARGETARCH" in \
      arm64) echo "79a3161eeb642f0473e23db6341f7baabd4a5933e921a9c1167c5d5c765c41a4";; \
      *) echo "158efc9ddfa1241fab5fb3526bb442c8dc6c4b1904d73213b9e4e93e03c52034";; \
    esac) && \
    curl --disable --retry 8 --retry-all-errors --retry-max-time 300 --remove-on-error --connect-timeout 15 --max-time 300 -fsSL -o /tmp/lazygit.tar.gz \
      "https://github.com/jesseduffield/lazygit/releases/download/v${LAZYGIT_VERSION}/lazygit_${LAZYGIT_VERSION}_linux_${LAZYGIT_ARCH}.tar.gz" && \
    echo "${LAZYGIT_SHA256}  /tmp/lazygit.tar.gz" | sha256sum -c - && \
    tar -C /tmp -xzf /tmp/lazygit.tar.gz lazygit && \
    install -m 0755 /tmp/lazygit /usr/local/bin/lazygit && \
    rm /tmp/lazygit /tmp/lazygit.tar.gz && \
    lazygit --version | grep -F "version=${LAZYGIT_VERSION}"

# ---------- delta (git diff pager) ----------
RUN DELTA_ARCH=$(case "$TARGETARCH" in arm64) echo "aarch64-unknown-linux-gnu";; *) echo "x86_64-unknown-linux-gnu";; esac) && \
    DELTA_SHA256=$(case "$TARGETARCH" in \
      arm64) echo "da7f4338f593572ff426ae153e0870e2fdc72729416eff551b40cdeb67940db8";; \
      *) echo "50f08c879f84c81ceb220e476491a7f492d2c9c671e79918cc44badf961a6240";; \
    esac) && \
    curl --disable --retry 8 --retry-all-errors --retry-max-time 300 --remove-on-error --connect-timeout 15 --max-time 300 -fsSL -o /tmp/delta.tar.gz \
      "https://github.com/dandavison/delta/releases/download/${DELTA_VERSION}/delta-${DELTA_VERSION}-${DELTA_ARCH}.tar.gz" && \
    echo "${DELTA_SHA256}  /tmp/delta.tar.gz" | sha256sum -c - && \
    tar -C /tmp -xzf /tmp/delta.tar.gz && \
    install -m 0755 "/tmp/delta-${DELTA_VERSION}-${DELTA_ARCH}/delta" /usr/local/bin/delta && \
    rm -rf /tmp/delta.tar.gz "/tmp/delta-${DELTA_VERSION}-${DELTA_ARCH}"

# ---------- eza (modern ls replacement) ----------
RUN EZA_ARCH=$(case "$TARGETARCH" in arm64) echo "aarch64";; *) echo "x86_64";; esac) && \
    EZA_SHA256=$(case "$TARGETARCH" in \
      arm64) echo "40b87ae8628aa2ff0f0d2dc24ab52f689631366385c3da630bae745671fd71ec";; \
      *) echo "35c70c5c43c29108075e58b893234c67ef585f0b53a7eaf8e9e7d4eec9f339b4";; \
    esac) && \
    curl --disable --retry 8 --retry-all-errors --retry-max-time 300 --remove-on-error --connect-timeout 15 --max-time 300 -fsSL -o /tmp/eza.tar.gz \
      "https://github.com/eza-community/eza/releases/download/v${EZA_VERSION}/eza_${EZA_ARCH}-unknown-linux-gnu.tar.gz" && \
    echo "${EZA_SHA256}  /tmp/eza.tar.gz" | sha256sum -c - && \
    tar -C /usr/local/bin -xzf /tmp/eza.tar.gz && \
    rm /tmp/eza.tar.gz

# ---------- Headless browser (Chromium + Xvfb + fonts) ----------
COPY --chmod=0755 scripts/validate_chromium_version.sh /usr/local/bin/validate-holycode-chromium-version
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-sandbox \
    xvfb \
    fonts-liberation2 fonts-dejavu-core fonts-noto-core fonts-noto-color-emoji \
    && test -u /usr/lib/chromium/chrome-sandbox \
    && dpkg-query -W -f='${Version}\n' chromium | grep -E '^(15[1-9]|1[6-9][0-9]|[2-9][0-9]{2})\.' \
    && test "$(dpkg --print-architecture)" = "$TARGETARCH" \
    && for package in chromium chromium-common chromium-sandbox; do \
      installed_version=$(dpkg-query -W -f='${Version}' "$package"); \
      validate-holycode-chromium-version "$installed_version" "linux/$TARGETARCH" "$RELEASE_VERSION" "$(date -u +%F)" || { echo "$package $installed_version violates the Chromium release policy" >&2; exit 1; }; \
    done \
    && test "$(dpkg-query -W -f='${Version}' chromium)" = "$(dpkg-query -W -f='${Version}' chromium-sandbox)" \
    && rm -rf /var/lib/apt/lists/*

# ---------- Python packages ----------
COPY config/python-requirements.lock /usr/local/share/holycode/python-requirements.lock
COPY config/python-seed-requirements.lock /usr/local/share/holycode/python-seed-requirements.lock
COPY scripts/verify_pip_vendor_record.py /tmp/verify-pip-vendor-record.py
COPY scripts/test_pip_vendor_urllib3.py /tmp/test_pip_vendor_urllib3.py
RUN python3 -m venv /tmp/holycode-pip-bootstrap && \
    /tmp/holycode-pip-bootstrap/bin/python -m pip install --no-cache-dir --upgrade \
      --require-hashes -r /usr/local/share/holycode/python-seed-requirements.lock && \
    /tmp/holycode-pip-bootstrap/bin/python -m pip install --no-cache-dir --upgrade \
      --target /usr/local/lib/python3.13/dist-packages \
      --require-hashes -r /usr/local/share/holycode/python-seed-requirements.lock && \
    install -m 0755 /tmp/holycode-pip-bootstrap/bin/pip /usr/local/bin/pip && \
    sed -i '1c#!/usr/bin/python3' /usr/local/bin/pip && \
    ln -sf pip /usr/local/bin/pip3 && \
    ln -sf pip /usr/local/bin/pip3.13 && \
    rm -rf /tmp/holycode-pip-bootstrap && \
    test "$(dpkg-query -W -f='${db:Status-Status}' python3-pip 2>/dev/null || true)" != installed && \
    test "$(dpkg-query -W -f='${db:Status-Status}' python3-setuptools 2>/dev/null || true)" != installed && \
    python3 -m pip install --no-cache-dir --break-system-packages --ignore-installed \
      --require-hashes -r /usr/local/share/holycode/python-requirements.lock

# Replace Debian's vulnerable wheel metadata after installing fixed copies in
# /usr/local. pip remains available from the exact PyPI package.
RUN python3 -m pip install --no-cache-dir --break-system-packages --ignore-installed \
      --require-hashes -r /usr/local/share/holycode/python-seed-requirements.lock && \
    python3 /tmp/verify-pip-vendor-record.py && \
    rm /tmp/verify-pip-vendor-record.py && \
    rm -rf /var/lib/apt/lists/* && \
    python3 -m pip --version | grep -F "pip ${PIP_VERSION}" && \
    python3 -c 'import pip._vendor.msgpack as msgpack; import pip._vendor.urllib3 as urllib3; assert msgpack.__version__ == "1.2.4"; assert urllib3.__version__ == "2.8.0"; assert msgpack.unpackb(msgpack.packb({"holycode": True})) == {"holycode": True}; import pip._vendor.pkg_resources' && \
    _PIP_USE_IMPORTLIB_METADATA=0 python3 -m pip list --format=json >/dev/null && \
    python3 -c 'import setuptools; assert setuptools.__version__ == "84.2.1"' && \
    python3 -m pip check && \
    python3 /tmp/test_pip_vendor_urllib3.py && \
    rm /tmp/test_pip_vendor_urllib3.py

RUN rm -f /usr/local/bin/dotenv

RUN npm install -g --ignore-scripts "npm@${NPM_VERSION}" && \
    test "$(npm --version)" = "${NPM_VERSION}" && \
    test "$(npm prefix -g)" = "/usr/local" && \
    npm ls -g brace-expansion tar ip-address --all >/dev/null && \
    rm -rf /root/.npm
# npm 12.2.2 owns the fixed brace-expansion, tar, and ip-address dependency graph.
# Exercise npm's official bundled node-gyp and Undici without replacements.
COPY scripts/test_node_gyp_download.mjs /tmp/test_node_gyp_download.mjs
COPY scripts/test_node_gyp_native.mjs /tmp/test_node_gyp_native.mjs
RUN node -e 'const npm=require("/usr/local/lib/node_modules/npm/package.json"); const gyp=require("/usr/local/lib/node_modules/npm/node_modules/node-gyp/package.json"); const undici=require("/usr/local/lib/node_modules/npm/node_modules/undici/package.json"); if(npm.version!=="12.2.2" || npm.dependencies["node-gyp"]!=="^13.0.0" || gyp.version!=="13.0.0" || gyp.dependencies.undici!=="^6.25.0" || undici.version!=="6.29.1") process.exit(1)' && \
    (cd /usr/local/lib/node_modules/npm && npm ls node-gyp undici --all >/dev/null) && \
    node /tmp/test_node_gyp_download.mjs && \
    node /tmp/test_node_gyp_native.mjs && \
    rm /tmp/test_node_gyp_download.mjs /tmp/test_node_gyp_native.mjs && \
    rm -rf /root/.npm

# ---------- OpenCode (AI coding agent) ----------
# Installed via npm as root (global install needs write access to /usr/local/lib)
RUN npm i -g --ignore-scripts "opencode-ai@${OPENCODE_VERSION}" "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}" \
      "@fission-ai/openspec@${OPENSPEC_VERSION}" && \
    rm -rf /root/.npm
ENV PATH="/home/opencode/.local/bin:${PATH}"

# Drizzle Kit's stable release still declares an unused legacy loader and older
# nested esbuild; remove both in the install layer and use the audited global pin.
RUN npm i -g --ignore-scripts \
    "typescript@${TYPESCRIPT_VERSION}" "tsx@${TSX_VERSION}" \
    "pnpm@${PNPM_VERSION}" \
    "vite@${VITE_VERSION}" esbuild@0.28.2 \
    "eslint@${ESLINT_VERSION}" "prettier@${PRETTIER_VERSION}" \
    nodemon@3.1.14 \
    dotenv-cli@11.0.0 \
    "wrangler@${WRANGLER_VERSION}" \
    pm2@7.1.2 \
    "prisma@${PRISMA_VERSION}" drizzle-kit@0.31.11 \
    "lighthouse@${LIGHTHOUSE_VERSION}" \
    json-server@0.17.4 http-server@14.1.1 && \
    DRIZZLE_DIR=/usr/local/lib/node_modules/drizzle-kit && \
    jq '.dependencies |= del(."@esbuild-kit/esm-loader") | .dependencies.esbuild = "0.28.2"' \
      "$DRIZZLE_DIR/package.json" > "$DRIZZLE_DIR/package.json.tmp" && \
    mv "$DRIZZLE_DIR/package.json.tmp" "$DRIZZLE_DIR/package.json" && \
    rm -rf \
      "$DRIZZLE_DIR/node_modules/@esbuild-kit" \
      "$DRIZZLE_DIR/node_modules/@esbuild" \
      "$DRIZZLE_DIR/node_modules/esbuild" && \
    ln -s ../../esbuild "$DRIZZLE_DIR/node_modules/esbuild" && \
    test "$(node -p 'require("/usr/local/lib/node_modules/drizzle-kit/node_modules/esbuild/package.json").version')" = "0.28.2" && \
    drizzle-kit --version && \
    drizzle-kit --help >/dev/null && \
    rm -rf /root/.npm

# Prisma 7.10.1 owns the current deepmerge-ts and mysql2 versions. Check the
# resolved owner graph and exercise the database driver without local overlays.
RUN test "$(npm view "@prisma/config@${PRISMA_VERSION}" dependencies.deepmerge-ts)" = "${PRISMA_DEEPMERGE_VERSION}" && \
    test "$(npm view "prisma@${PRISMA_VERSION}" dependencies.mysql2)" = "${PRISMA_MYSQL2_VERSION}" && \
    node -e 'const fs=require("node:fs"); const path=require("node:path"); const root="/usr/local/lib/node_modules/prisma"; const configPath=require.resolve("@prisma/config/package.json",{paths:[root]}); const config=require(configPath); const packageMetadata=(name,base)=>{const entry=require.resolve(name,{paths:[base]}); let directory=path.dirname(entry); while(directory!==path.dirname(directory)){const manifest=path.join(directory,"package.json"); if(fs.existsSync(manifest)){const metadata=JSON.parse(fs.readFileSync(manifest,"utf8")); if(metadata.name===name)return metadata;} directory=path.dirname(directory);} throw Error("Unable to find "+name+" manifest from resolved entry "+entry);}; const deepmerge=packageMetadata("deepmerge-ts",configPath); const prisma=require(root+"/package.json"); const mysql2=packageMetadata("mysql2",root); if(config.dependencies["deepmerge-ts"]!==process.argv[1] || deepmerge.version!==process.argv[1] || prisma.dependencies.mysql2!==process.argv[2] || mysql2.version!==process.argv[2]) process.exit(1)' \
      "${PRISMA_DEEPMERGE_VERSION}" "${PRISMA_MYSQL2_VERSION}" && \
    (cd /usr/local/lib/node_modules/prisma && npm ls @prisma/config deepmerge-ts mysql2 --all >/dev/null) && \
    node -e 'const mysql=require("/usr/local/lib/node_modules/prisma/node_modules/mysql2"); if(typeof mysql.createConnection!=="function") process.exit(1)' && \
    prisma --version >/dev/null && \
    rm -rf /root/.npm

# PM2's official owner graph now pins the fixed js-yaml release.
RUN test "$(npm view pm2@7.1.2 dependencies.js-yaml)" = "${PM2_JS_YAML_VERSION}" && \
    node -e 'const pkg=require("/usr/local/lib/node_modules/pm2/package.json"); const yaml=require("/usr/local/lib/node_modules/pm2/node_modules/js-yaml/package.json"); if(pkg.version!=="7.1.2" || pkg.dependencies["js-yaml"]!==process.argv[1] || yaml.version!==process.argv[1]) process.exit(1)' "${PM2_JS_YAML_VERSION}" && \
    (cd /usr/local/lib/node_modules/pm2 && npm ls js-yaml --all >/dev/null) && \
    node -e 'const yaml=require("/usr/local/lib/node_modules/pm2/node_modules/js-yaml"); const parsed=yaml.load("service:\n  enabled: true\n"); if(parsed.service.enabled!==true) process.exit(1)' && \
    PM2_APP=/tmp/holycode-build-pm2-app.js && \
    printf 'setInterval(() => {}, 60000);\n' > "$PM2_APP" && \
    PM2_HOME=/tmp/holycode-build-pm2 pm2 start "$PM2_APP" --name holycode-build-pm2 --no-autorestart >/dev/null && \
    PM2_HOME=/tmp/holycode-build-pm2 pm2 --version | grep -Fx "7.1.2" && \
    PM2_HOME=/tmp/holycode-build-pm2 pm2 stop holycode-build-pm2 >/dev/null && \
    PM2_HOME=/tmp/holycode-build-pm2 pm2 kill >/dev/null && \
    rm -rf /tmp/holycode-build-pm2 "$PM2_APP" && \
    rm -rf /root/.npm

# PM2 7.1.2 no longer owns the get-uri/basic-ftp transport graph.
RUN npm ls -g pm2 --all >/dev/null && \
    test ! -d /usr/local/lib/node_modules/pm2/node_modules/get-uri && \
    test ! -d /usr/local/lib/node_modules/pm2/node_modules/basic-ftp && \
    rm -rf /root/.npm

# Wrangler 4.157.0 owns Miniflare 5.20261103.0-beta and workerd 1.20261103.1;
# Miniflare owns the same workerd and the fixed Sharp release. Bind each owner.
RUN WRANGLER_SHARP_INTEGRITY="sha512-Ywn4OnzGukp7CDMrp08RQ50YKmuwG47brZgIVPTvBaaAfQlRlygrRqSrxdCiL9M+LlzLBiJ68IR1QqvzHyjC7g==" && \
    test "$(npm view "sharp@${WRANGLER_SHARP_VERSION}" dist.integrity)" = "$WRANGLER_SHARP_INTEGRITY" && \
    test "$(npm view "wrangler@${WRANGLER_VERSION}" dependencies.miniflare)" = "${WRANGLER_MINIFLARE_VERSION}" && \
    test "$(npm view "wrangler@${WRANGLER_VERSION}" dependencies.workerd)" = "1.20261103.1" && \
    test "$(npm view "wrangler@${WRANGLER_VERSION}" dependencies.esbuild)" = "0.28.2" && \
    test "$(npm view "miniflare@${WRANGLER_MINIFLARE_VERSION}" dependencies.sharp)" = "${WRANGLER_SHARP_VERSION}" && \
    test "$(npm view "miniflare@${WRANGLER_MINIFLARE_VERSION}" dependencies.workerd)" = "1.20261103.1" && \
    WRANGLER_PACKAGE=/usr/local/lib/node_modules/wrangler/package.json && \
    WRANGLER_NODE_MODULES=/usr/local/lib/node_modules/wrangler/node_modules && \
    WRANGLER_MINIFLARE_PACKAGE="$WRANGLER_NODE_MODULES/miniflare/package.json" && \
    WRANGLER_WORKERD_PACKAGE="$WRANGLER_NODE_MODULES/workerd/package.json" && \
    WRANGLER_SHARP_DIR="$WRANGLER_NODE_MODULES/sharp" && \
    test "$(node -p 'require(process.argv[1]).version' "$WRANGLER_PACKAGE")" = "${WRANGLER_VERSION}" && \
    node -e 'const pkg=require(process.argv[1]); if(pkg.dependencies.miniflare!==process.argv[2] || pkg.dependencies.workerd!=="1.20261103.1" || pkg.dependencies.esbuild!=="0.28.2") process.exit(1)' \
      "$WRANGLER_PACKAGE" "${WRANGLER_MINIFLARE_VERSION}" && \
    node -e 'const pkg=require(process.argv[1]); if(pkg.version!==process.argv[2] || pkg.dependencies.sharp!==process.argv[3]) process.exit(1)' \
      "$WRANGLER_MINIFLARE_PACKAGE" "${WRANGLER_MINIFLARE_VERSION}" "${WRANGLER_SHARP_VERSION}" && \
    node -e 'const pkg=require(process.argv[1]); if(pkg.dependencies.workerd!=="1.20261103.1") process.exit(1)' \
      "$WRANGLER_MINIFLARE_PACKAGE" && \
    test "$(node -p 'require(process.argv[1]).version' "$WRANGLER_WORKERD_PACKAGE")" = \
      "1.20261103.1" && \
    test "$(node -p 'require(process.argv[1]).version' "$WRANGLER_SHARP_DIR/package.json")" = \
      "${WRANGLER_SHARP_VERSION}" && \
    case "${TARGETARCH}" in \
      amd64) WRANGLER_SHARP_ARCH=x64; \
        WRANGLER_SHARP_NATIVE_INTEGRITY="sha512-SxFtLTeJInhAA9Q836kux2vZNeOBQEx658qvbboZScr0wIARym3IcGmW7KpVD5sbVg0Ojy+udFQdayYIZyoNog=="; \
        WRANGLER_SHARP_LIBVIPS_INTEGRITY="sha512-GJ//SSXbnwSDes02umB3nDJLFcQzw8a18V8fyhqr6tV515tOEMdImjjxj1AoafMRz56F3PHgftnj1QEKSU1zkw==";; \
      arm64) WRANGLER_SHARP_ARCH=arm64; \
        WRANGLER_SHARP_NATIVE_INTEGRITY="sha512-LYVx5JTsOM2CBzmxreh+nl64/3H6Xb09iSLknqH47z2T2DFFxDeFLP5y4dJwe6H7uGQlHPyEEtIqyo3DYsRwdQ=="; \
        WRANGLER_SHARP_LIBVIPS_INTEGRITY="sha512-Y3dgX/6lE2QhQb+Gxy0WZxfg9MEm/JBjamZpS2IklP7xIQoKN4hzAm7KcMVGtaVDt3neE9OKBC7vAfonA/Lr1A==";; \
      *) echo "unsupported Sharp target architecture: ${TARGETARCH}" >&2; exit 1;; \
    esac && \
    WRANGLER_SHARP_NATIVE_PACKAGE="@img/sharp-linux-${WRANGLER_SHARP_ARCH}" && \
    WRANGLER_SHARP_LIBVIPS_PACKAGE="@img/sharp-libvips-linux-${WRANGLER_SHARP_ARCH}" && \
    WRANGLER_SHARP_NATIVE_DIR="$WRANGLER_NODE_MODULES/@img/sharp-linux-${WRANGLER_SHARP_ARCH}" && \
    WRANGLER_SHARP_LIBVIPS_DIR="$WRANGLER_NODE_MODULES/@img/sharp-libvips-linux-${WRANGLER_SHARP_ARCH}" && \
    node -e 'const pkg=require(process.argv[1]); if(pkg.version!==process.argv[2] || pkg.optionalDependencies[process.argv[3]]!==process.argv[4]) process.exit(1)' \
      "$WRANGLER_SHARP_NATIVE_DIR/package.json" "${WRANGLER_SHARP_VERSION}" \
      "$WRANGLER_SHARP_LIBVIPS_PACKAGE" "${WRANGLER_SHARP_LIBVIPS_VERSION}" && \
    test "$(node -p 'require(process.argv[1]).version' "$WRANGLER_SHARP_LIBVIPS_DIR/package.json")" = \
      "${WRANGLER_SHARP_LIBVIPS_VERSION}" && \
    test "$(npm view "${WRANGLER_SHARP_NATIVE_PACKAGE}@${WRANGLER_SHARP_VERSION}" dist.integrity)" = \
      "$WRANGLER_SHARP_NATIVE_INTEGRITY" && \
    test "$(npm view "${WRANGLER_SHARP_LIBVIPS_PACKAGE}@${WRANGLER_SHARP_LIBVIPS_VERSION}" dist.integrity)" = \
      "$WRANGLER_SHARP_LIBVIPS_INTEGRITY" && \
    WRANGLER_SHARP_TARBALL=$(npm pack --silent --ignore-scripts --pack-destination /tmp \
      "sharp@${WRANGLER_SHARP_VERSION}") && \
    WRANGLER_SHARP_NATIVE_TARBALL=$(npm pack --silent --ignore-scripts --pack-destination /tmp \
      "${WRANGLER_SHARP_NATIVE_PACKAGE}@${WRANGLER_SHARP_VERSION}") && \
    WRANGLER_SHARP_LIBVIPS_TARBALL=$(npm pack --silent --ignore-scripts --pack-destination /tmp \
      "${WRANGLER_SHARP_LIBVIPS_PACKAGE}@${WRANGLER_SHARP_LIBVIPS_VERSION}") && \
    node -e 'const fs=require("fs"); const crypto=require("crypto"); const actual=`sha512-${crypto.createHash("sha512").update(fs.readFileSync(process.argv[1])).digest("base64")}`; if(actual!==process.argv[2]) process.exit(1)' \
      "/tmp/${WRANGLER_SHARP_TARBALL}" "$WRANGLER_SHARP_INTEGRITY" && \
    node -e 'const fs=require("fs"); const crypto=require("crypto"); const actual=`sha512-${crypto.createHash("sha512").update(fs.readFileSync(process.argv[1])).digest("base64")}`; if(actual!==process.argv[2]) process.exit(1)' \
      "/tmp/${WRANGLER_SHARP_NATIVE_TARBALL}" "$WRANGLER_SHARP_NATIVE_INTEGRITY" && \
    node -e 'const fs=require("fs"); const crypto=require("crypto"); const actual=`sha512-${crypto.createHash("sha512").update(fs.readFileSync(process.argv[1])).digest("base64")}`; if(actual!==process.argv[2]) process.exit(1)' \
      "/tmp/${WRANGLER_SHARP_LIBVIPS_TARBALL}" "$WRANGLER_SHARP_LIBVIPS_INTEGRITY" && \
    WRANGLER_SHARP_VERIFIED_DIR=/tmp/holycode-wrangler-sharp-verified && \
    WRANGLER_SHARP_NATIVE_VERIFIED_DIR=/tmp/holycode-wrangler-sharp-native-verified && \
    WRANGLER_SHARP_LIBVIPS_VERIFIED_DIR=/tmp/holycode-wrangler-sharp-libvips-verified && \
    mkdir "$WRANGLER_SHARP_VERIFIED_DIR" "$WRANGLER_SHARP_NATIVE_VERIFIED_DIR" \
      "$WRANGLER_SHARP_LIBVIPS_VERIFIED_DIR" && \
    tar -xzf "/tmp/${WRANGLER_SHARP_TARBALL}" -C "$WRANGLER_SHARP_VERIFIED_DIR" && \
    tar -xzf "/tmp/${WRANGLER_SHARP_NATIVE_TARBALL}" -C "$WRANGLER_SHARP_NATIVE_VERIFIED_DIR" && \
    tar -xzf "/tmp/${WRANGLER_SHARP_LIBVIPS_TARBALL}" -C "$WRANGLER_SHARP_LIBVIPS_VERIFIED_DIR" && \
    diff -qr --no-dereference "$WRANGLER_SHARP_VERIFIED_DIR/package" "$WRANGLER_SHARP_DIR" && \
    diff -qr --no-dereference "$WRANGLER_SHARP_NATIVE_VERIFIED_DIR/package" "$WRANGLER_SHARP_NATIVE_DIR" && \
    diff -qr --no-dereference "$WRANGLER_SHARP_LIBVIPS_VERIFIED_DIR/package" "$WRANGLER_SHARP_LIBVIPS_DIR" && \
    rm -rf "$WRANGLER_SHARP_VERIFIED_DIR" "$WRANGLER_SHARP_NATIVE_VERIFIED_DIR" \
      "$WRANGLER_SHARP_LIBVIPS_VERIFIED_DIR" && \
    rm "/tmp/${WRANGLER_SHARP_TARBALL}" "/tmp/${WRANGLER_SHARP_NATIVE_TARBALL}" \
      "/tmp/${WRANGLER_SHARP_LIBVIPS_TARBALL}" && \
    test "$(find /usr/local/lib/node_modules/wrangler -path '*/sharp/package.json' -type f | wc -l)" -eq 1 && \
    test "$(find /usr/local/lib/node_modules/wrangler -path "*/@img/sharp-linux-${WRANGLER_SHARP_ARCH}/package.json" -type f | wc -l)" -eq 1 && \
    test "$(find /usr/local/lib/node_modules/wrangler -path "*/@img/sharp-libvips-linux-${WRANGLER_SHARP_ARCH}/package.json" -type f | wc -l)" -eq 1 && \
    (cd /usr/local/lib/node_modules/wrangler && npm ls sharp --all >/dev/null) && \
    node -e 'const sharp=require(process.argv[1]); if(sharp.versions.sharp!==process.argv[2] || sharp.versions.heif!=="1.23.5") process.exit(1); sharp({create:{width:2,height:2,channels:4,background:{r:220,g:30,b:30,alpha:1}}}).avif().toBuffer().then(buffer=>sharp(buffer).raw().toBuffer({resolveWithObject:true})).then(({data,info})=>{if(info.width!==2 || info.height!==2 || info.channels!==4 || data.length!==16) process.exit(1)}).catch(error=>{console.error(error);process.exit(1)})' \
      "$WRANGLER_SHARP_DIR" "${WRANGLER_SHARP_VERSION}" && \
    ! command -v sharp && \
    rm -rf /root/.npm

RUN npm i -g --ignore-scripts \
    "paperclipai@${PAPERCLIP_VERSION}" && \
    rm -rf /root/.npm
# Paperclip's current Cursor SDK no longer installs Connect's Node transport.
# The remaining Undici is jsdom's 8.x dependency; guard the resolved owners.
RUN test "$(npm view "@cursor/sdk@${PAPERCLIP_CURSOR_SDK_VERSION}" dist.integrity)" = \
      "sha512-Mn0gK8V+5BkOqm22J2ocU+1BrqnNH8QcK9kmA7SkRuawDOeq2ABC2BIZq9gRnF3z68x/I7J/ZU8jl6DcshCVUA==" && \
    test "$(npm view "jsdom@${PAPERCLIP_JSDOM_VERSION}" dist.integrity)" = \
      "sha512-hQMUPvRgN7KxsfIytDQji7bimuJeRQa6Qo5+iuiZQk5CafeRxLIA10/cG5YCBFNpD9RO3oqIiN4CO1Y44kxqXg==" && \
    test "$(npm view "undici@${PAPERCLIP_UNDICI_VERSION}" dist.integrity)" = \
      "sha512-+fdndUTwBP86cVjihTp21hZHo7d6oj1c/47XPA3lL8mM0XHs+C4EkcjmgRsFnFk2f/UONGDy9ItBItmXsLOQHw==" && \
    CONNECT_NODE_PACKAGE=/usr/local/lib/node_modules/paperclipai/node_modules/@connectrpc/connect-node/package.json && \
    test ! -e "$CONNECT_NODE_PACKAGE" && \
    test "$(find /usr/local/lib/node_modules/paperclipai -path '*/@connectrpc/connect-node/package.json' -type f | wc -l)" -eq 0 && \
    test "$(find /usr/local/lib/node_modules/paperclipai -path '*/undici/package.json' -type f | wc -l)" -eq 1 && \
    node -e 'const root="/usr/local/lib/node_modules/paperclipai/node_modules"; const adapter=require(`${root}/@paperclipai/adapter-cursor-cloud/package.json`); const sdk=require(`${root}/@cursor/sdk/package.json`); const server=require(`${root}/@paperclipai/server/package.json`); const jsdom=require(`${root}/jsdom/package.json`); const undici=require(`${root}/undici/package.json`); const fail=(name,expected,actual)=>{console.error(`${name}: expected ${expected}, got ${actual}`);process.exit(1)}; if(sdk.version!==process.argv[1]) fail("Paperclip Cursor SDK version mismatch",process.argv[1],sdk.version); if(adapter.dependencies["@cursor/sdk"]!=="^1.0.28" || sdk.dependencies["@connectrpc/connect-node"]!==undefined || server.dependencies.jsdom!=="^30.0.1") process.exit(1); if(jsdom.version!==process.argv[2]) fail("Paperclip jsdom version mismatch",process.argv[2],jsdom.version); if(jsdom.dependencies.undici!=="^8.12.1") fail("Paperclip jsdom Undici range mismatch","^8.12.1",jsdom.dependencies.undici); if(undici.version!==process.argv[3]) fail("Paperclip Undici resolved version mismatch",process.argv[3],undici.version)' \
      "${PAPERCLIP_CURSOR_SDK_VERSION}" "${PAPERCLIP_JSDOM_VERSION}" "${PAPERCLIP_UNDICI_VERSION}" && \
    node -e 'const root="/usr/local/lib/node_modules/paperclipai/node_modules"; if(require.resolve("undici/package.json",{paths:[`${root}/jsdom`]})!==`${root}/undici/package.json`) process.exit(1)' && \
    (cd /usr/local/lib/node_modules/paperclipai && npm ls @cursor/sdk jsdom undici --omit=dev --all >/dev/null) && \
    node -e 'const fs=require("fs"); const root="/usr/local/lib/node_modules/paperclipai/node_modules/@cursor/sdk"; const {Agent,Cursor}=require(root); const agentTypes=fs.readFileSync(`${root}/dist/esm/agent.d.ts`,"utf8"); const runTypes=fs.readFileSync(`${root}/dist/esm/run.d.ts`,"utf8"); if([Agent.create,Agent.resume,Agent.getRun,Cursor.me,Cursor.models?.list].some(fn=>typeof fn!=="function") || !agentTypes.includes("send(message:") || !agentTypes.includes("[Symbol.asyncDispose]()") || !runTypes.includes("supports(operation:") || !runTypes.includes("stream():") || !runTypes.includes("wait():")) process.exit(1)' && \
    node --input-type=module -e 'const {testEnvironment}=await import("file:///usr/local/lib/node_modules/paperclipai/node_modules/@paperclipai/adapter-cursor-cloud/dist/server/index.js"); const result=await testEnvironment({adapterType:"cursor_cloud",config:{}}); if(result.status!=="fail" || !result.checks.some((check)=>check.code==="cursor_cloud_api_key_missing")) process.exit(1)' && \
    rm -rf /root/.npm
# Package the supported Claude Auth plugin for network-free startup.
RUN test "$(npm view "opencode-claude-auth@${CLAUDE_AUTH_PLUGIN_VERSION}" dist.integrity)" = \
      "sha512-iEXMVh2J/l8ZlNiMNp7QmtGQtAwjXgaSgXvA2zZzJbUZEOBKvuoq9gKRtqSjYB3faDwOVwwiGAj+S2N/8sgolA==" && \
    CLAUDE_AUTH_TARBALL=$(npm pack --silent --pack-destination /tmp \
      "opencode-claude-auth@${CLAUDE_AUTH_PLUGIN_VERSION}") && \
    CLAUDE_AUTH_DIR=/usr/local/share/holycode/plugins/opencode-claude-auth && \
    mkdir -p "${CLAUDE_AUTH_DIR}" && \
    tar -xzf "/tmp/${CLAUDE_AUTH_TARBALL}" -C "${CLAUDE_AUTH_DIR}" --strip-components=1 && \
    rm "/tmp/${CLAUDE_AUTH_TARBALL}" && \
    test "$(node -p 'require(process.argv[1]).version' "${CLAUDE_AUTH_DIR}/package.json")" = \
      "${CLAUDE_AUTH_PLUGIN_VERSION}" && \
    rm -rf /root/.npm
RUN find /usr/local/lib/node_modules/paperclipai/node_modules/@embedded-postgres \
      -path '*/native/lib' -type d -exec sh -c '\
        for lib_dir do \
          [ -f "$lib_dir/libcrypto.so.1.1" ] && ln -sf libcrypto.so.1.1 "$lib_dir/libcrypto.so.1"; \
          [ -f "$lib_dir/libssl.so.1.1" ] && ln -sf libssl.so.1.1 "$lib_dir/libssl.so.1"; \
        done' sh {} +
# npm 12 blocks dependency lifecycle scripts unless they are explicitly reviewed.
# Allow only the exact OpenCode, Claude, and architecture-specific embedded
# PostgreSQL scripts required at runtime; validate every allowed and blocked pin.
COPY config/npm-global-script-policy.json /usr/local/share/holycode/npm-global-script-policy.json
COPY scripts/validate_npm_script_policy.py /usr/local/bin/validate-npm-script-policy
RUN chmod +x /usr/local/bin/validate-npm-script-policy
RUN python3 /usr/local/bin/validate-npm-script-policy \
      --policy /usr/local/share/holycode/npm-global-script-policy.json \
      --root /usr/local/lib/node_modules \
      --target-arch "${TARGETARCH}" && \
    (cd /usr/local/lib/node_modules/opencode-ai && node ./postinstall.mjs) && \
    (cd /usr/local/lib/node_modules/@anthropic-ai/claude-code && node install.cjs) && \
    POSTGRES_PACKAGE=$(find /usr/local/lib/node_modules/paperclipai/node_modules/@embedded-postgres \
      -mindepth 1 -maxdepth 1 -type d -name 'linux-*' -print -quit) && \
    test -n "$POSTGRES_PACKAGE" && \
    (cd "$POSTGRES_PACKAGE" && node scripts/hydrate-symlinks.js) && \
    node -e 'const fs=require("fs"); const path=require("path"); const root=process.argv[1]; const links=JSON.parse(fs.readFileSync(path.join(root,"native/pg-symlinks.json"),"utf8")); for (const {source,target} of links) { const sourcePath=path.join(root,source); const targetPath=path.join(root,target); if (!fs.lstatSync(targetPath).isSymbolicLink() || fs.realpathSync(targetPath)!==fs.realpathSync(sourcePath)) throw new Error(`invalid PostgreSQL link: ${target}`); }' \
      "$POSTGRES_PACKAGE" && \
    opencode --version | grep -Fx "${OPENCODE_VERSION}" && \
    claude --version | grep -F "${CLAUDE_CODE_VERSION}" && \
    esbuild --version | grep -Fx "0.28.2" && \
    prisma --version >/dev/null && \
    wrangler --version | grep -F "${WRANGLER_VERSION}" && \
    ! command -v vercel && ! command -v sharp && ! command -v concurrently && \
    ! command -v lhci && ! command -v netlify && ! command -v serve && \
    WORKERD_BIN=$(find /usr/local/lib/node_modules/wrangler -path '*/workerd/bin/workerd' -type f -print -quit) && \
    test -n "${WORKERD_BIN}" && "${WORKERD_BIN}" --version >/dev/null && \
    node -e 'const ssh2=require("/usr/local/lib/node_modules/paperclipai/node_modules/ssh2"); if(typeof ssh2.Client!=="function") process.exit(1)' && \
    rm -rf /root/.npm

COPY scripts/verify_pip_vendor_record.py /tmp/verify_pip_vendor_record.py
COPY scripts/test_pip_vendor_urllib3.py /tmp/test_pip_vendor_urllib3.py
RUN mkdir -p /usr/local/share/holycode/python-seed && \
    python3 -m pip download --no-deps --only-binary=:all: \
      --dest /usr/local/share/holycode/python-seed \
      --require-hashes -r /usr/local/share/holycode/python-seed-requirements.lock && \
    python3 -m venv /tmp/holycode-pip-seed-check && \
    /tmp/holycode-pip-seed-check/bin/python -m pip install --no-index --no-deps \
      --find-links /usr/local/share/holycode/python-seed \
      "pip==${PIP_VERSION}" "setuptools==${SETUPTOOLS_VERSION}" \
      "packaging==26.3" "wheel==0.48.0" && \
    /tmp/holycode-pip-seed-check/bin/python /tmp/verify_pip_vendor_record.py && \
    /tmp/holycode-pip-seed-check/bin/python /tmp/test_pip_vendor_urllib3.py && \
    /tmp/holycode-pip-seed-check/bin/python -c 'import pip._vendor.msgpack as m,pip._vendor.urllib3 as u; import pip._vendor.pkg_resources as p; assert m.__version__=="1.2.4" and u.__version__=="2.8.0" and p.get_distribution("pip").version=="26.3"' && \
    rm -rf /tmp/holycode-pip-seed-check \
      /tmp/verify_pip_vendor_record.py /tmp/test_pip_vendor_urllib3.py

RUN mkdir -p /usr/local/share/holycode && \
    dpkg-query -W -f='${binary:Package}\t${Version}\n' | sort > /usr/local/share/holycode/dpkg-inventory.txt

# ---------- Copy config files ----------
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY scripts/bootstrap.sh /usr/local/bin/bootstrap.sh
COPY config/opencode.json /usr/local/share/holycode/opencode.json
COPY THIRD-PARTY-NOTICES /usr/local/share/holycode/THIRD-PARTY-NOTICES
RUN install -d -m 0755 /usr/local/share/holycode/skills \
    && chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/bootstrap.sh

# ---------- s6-overlay service: opencode web ----------
COPY s6-overlay/s6-rc.d/opencode/type /etc/s6-overlay/s6-rc.d/opencode/type
COPY s6-overlay/s6-rc.d/opencode/run /etc/s6-overlay/s6-rc.d/opencode/run
RUN chmod +x /etc/s6-overlay/s6-rc.d/opencode/run && \
    touch /etc/s6-overlay/user-bundles.d/user/contents.d/opencode

# ---------- s6-overlay service: xvfb ----------
COPY s6-overlay/s6-rc.d/xvfb/type /etc/s6-overlay/s6-rc.d/xvfb/type
COPY s6-overlay/s6-rc.d/xvfb/run /etc/s6-overlay/s6-rc.d/xvfb/run
RUN chmod +x /etc/s6-overlay/s6-rc.d/xvfb/run && \
    touch /etc/s6-overlay/user-bundles.d/user/contents.d/xvfb

COPY s6-overlay/s6-rc.d/paperclip/type /etc/s6-overlay/s6-rc.d/paperclip/type
COPY s6-overlay/s6-rc.d/paperclip/run /etc/s6-overlay/s6-rc.d/paperclip/run
RUN chmod +x /etc/s6-overlay/s6-rc.d/paperclip/run

# ---------- Working directory ----------
WORKDIR /workspace

# ---------- Expose web UI port ----------
EXPOSE 4096

# ---------- Health check ----------
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -sf http://localhost:4096/ || exit 1

# ---------- s6-overlay as PID 1 ----------
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
