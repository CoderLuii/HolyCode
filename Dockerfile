# ==============================================================================
# HolyCode - Pre-configured Docker Environment for OpenCode
# https://github.com/coderluii/holycode
# ==============================================================================

# renovate: datasource=github-releases depName=cli/cli
ARG GITHUB_CLI_VERSION=2.96.0
ARG GITHUB_CLI_REF=b300f2ec7ec9dc9addc39b2ad88c54097ded7ca0

# GitHub CLI 2.96.0 was released before Go 1.26.5 fixed CVE-2026-39822.
# Rebuild the exact upstream tag with the fixed toolchain until GitHub ships it.
FROM golang:1.26.5-trixie@sha256:4ee9ffa999b4583ce281939cdff828763083610292f252279a0cee77473bd9a7 AS github-cli-builder
ARG GITHUB_CLI_VERSION
ARG GITHUB_CLI_REF
RUN git clone --branch "v${GITHUB_CLI_VERSION}" --depth 1 \
      https://github.com/cli/cli.git /src && \
    cd /src && \
    test "$(git rev-parse HEAD)" = "${GITHUB_CLI_REF}" && \
    test "$(git describe --tags --exact-match HEAD)" = "v${GITHUB_CLI_VERSION}" && \
    SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)" \
      GH_VERSION="${GITHUB_CLI_VERSION}" go run ./script/build.go bin/gh && \
    install -D -m 0755 bin/gh /out/gh && \
    go version -m /out/gh | grep -F "go1.26.5" && \
    /out/gh --version | grep -F "gh version ${GITHUB_CLI_VERSION}"

FROM node:24.18.0-trixie-slim@sha256:ae91dcc111a68c9d2d81ff2a17bda61be126426176fde6fe7d08ab13b7f50573

# ---------- Build args ----------
ARG GITHUB_CLI_VERSION
ARG S6_OVERLAY_VERSION=3.2.3.2
ARG FZF_VERSION=0.74.1
ARG LAZYGIT_VERSION=0.63.1
ARG DELTA_VERSION=0.19.2
ARG EZA_VERSION=0.23.5
# renovate: datasource=npm depName=opencode-ai
ARG OPENCODE_VERSION=1.18.4
# renovate: datasource=npm depName=@anthropic-ai/claude-code
ARG CLAUDE_CODE_VERSION=2.1.216
# renovate: datasource=npm depName=paperclipai
ARG PAPERCLIP_VERSION=2026.707.0
# renovate: datasource=npm depName=undici
ARG PAPERCLIP_UNDICI_VERSION=6.27.0
# renovate: datasource=npm depName=typescript
ARG TYPESCRIPT_VERSION=6.0.3
# renovate: datasource=npm depName=npm
ARG NPM_VERSION=12.0.1
# renovate: datasource=npm depName=tsx
ARG TSX_VERSION=4.23.1
# renovate: datasource=npm depName=pnpm
ARG PNPM_VERSION=11.15.1
# renovate: datasource=npm depName=vite
ARG VITE_VERSION=8.1.5
# renovate: datasource=npm depName=prettier
ARG PRETTIER_VERSION=3.9.6
# renovate: datasource=npm depName=prisma
ARG PRISMA_VERSION=7.9.0
# renovate: datasource=npm depName=lighthouse
ARG LIGHTHOUSE_VERSION=13.4.1
# renovate: datasource=npm depName=wrangler
ARG WRANGLER_VERSION=4.112.0
# renovate: datasource=npm depName=netlify-cli
ARG NETLIFY_CLI_VERSION=26.2.0
# renovate: datasource=pypi depName=numpy
ARG NUMPY_VERSION=2.5.1
# renovate: datasource=pypi depName=pip
ARG PIP_VERSION=26.1.2
ARG RELEASE_APT_REFRESH=2026-07-21
ARG TARGETARCH

LABEL org.opencontainers.image.source=https://github.com/CoderLuii/HolyCode \
    io.holycode.version.github-cli=${GITHUB_CLI_VERSION} \
    io.holycode.version.opencode=${OPENCODE_VERSION} \
    io.holycode.version.claude-code=${CLAUDE_CODE_VERSION} \
    io.holycode.version.paperclip=${PAPERCLIP_VERSION} \
    io.holycode.version.npm=${NPM_VERSION} \
    io.holycode.version.typescript=${TYPESCRIPT_VERSION} \
    io.holycode.version.tsx=${TSX_VERSION} \
    io.holycode.version.pnpm=${PNPM_VERSION} \
    io.holycode.version.vite=${VITE_VERSION} \
    io.holycode.version.prettier=${PRETTIER_VERSION} \
    io.holycode.version.prisma=${PRISMA_VERSION} \
    io.holycode.version.lighthouse=${LIGHTHOUSE_VERSION} \
    io.holycode.version.s6-overlay=${S6_OVERLAY_VERSION} \
    io.holycode.version.fzf=${FZF_VERSION} \
    io.holycode.version.wrangler=${WRANGLER_VERSION} \
    io.holycode.version.netlify-cli=${NETLIFY_CLI_VERSION} \
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

# ---------- s6-overlay v3 (multi-arch) ----------
RUN test -n "${RELEASE_APT_REFRESH}" && apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends xz-utils curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*
RUN S6_ARCH=$(case "$TARGETARCH" in arm64) echo "aarch64";; *) echo "x86_64";; esac) && \
    S6_ARCH_SHA256=$(case "$TARGETARCH" in \
      arm64) echo "b17f17a82e7a515c682a91edaf2ffdabb73f891981b6c1fd712115693a2f8b4c";; \
      *) echo "e6befcc96a437a3831386ecfc51808c5d3e939dc5fe3c02ae9284599e8aa2408";; \
    esac) && \
    curl -fsSL -o /tmp/s6-overlay-noarch.tar.xz \
      "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz" && \
    curl -fsSL -o /tmp/s6-overlay-arch.tar.xz \
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
      arm64) echo "f22204dd1a091d43e102268d062fd53b47133c8d8581671ee5eb225b75e31183";; \
      *) echo "df53438be5f51e151bb4044d78fda72bdfe209e3ecd2baecae48e8dea370c81b";; \
    esac) && \
    curl -fsSL -o /tmp/fzf.tar.gz \
      "https://github.com/junegunn/fzf/releases/download/v${FZF_VERSION}/fzf-${FZF_VERSION}-linux_${TARGETARCH}.tar.gz" && \
    echo "${FZF_SHA256}  /tmp/fzf.tar.gz" | sha256sum -c - && \
    tar -C /usr/local/bin -xzf /tmp/fzf.tar.gz fzf && \
    rm /tmp/fzf.tar.gz

# ---------- Python 3 (for user projects) ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends \
    pandoc ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# ---------- GitHub CLI ----------
COPY --from=github-cli-builder /out/gh /usr/local/bin/gh
RUN gh --version | grep -F "gh version ${GITHUB_CLI_VERSION}"

# ---------- lazygit ----------
RUN LAZYGIT_ARCH=$(case "$TARGETARCH" in arm64) echo "arm64";; *) echo "x86_64";; esac) && \
    LAZYGIT_SHA256=$(case "$TARGETARCH" in \
      arm64) echo "555dbc9a8efcf2e33bc24e7fbd9463e9fa375e3c5e23cc270763733c38eeae36";; \
      *) echo "8e033bc78c8e192dee9510e951f6c9e154289b7198d22c924ed1d0a951b0dac1";; \
    esac) && \
    curl -fsSL -o /tmp/lazygit.tar.gz \
      "https://github.com/jesseduffield/lazygit/releases/download/v${LAZYGIT_VERSION}/lazygit_${LAZYGIT_VERSION}_Linux_${LAZYGIT_ARCH}.tar.gz" && \
    echo "${LAZYGIT_SHA256}  /tmp/lazygit.tar.gz" | sha256sum -c - && \
    tar -C /usr/local/bin -xzf /tmp/lazygit.tar.gz lazygit && \
    rm /tmp/lazygit.tar.gz

# ---------- delta (git diff pager) ----------
RUN DELTA_ARCH=$(case "$TARGETARCH" in arm64) echo "aarch64-unknown-linux-gnu";; *) echo "x86_64-unknown-linux-gnu";; esac) && \
    DELTA_SHA256=$(case "$TARGETARCH" in \
      arm64) echo "0bfce159a5cddd5feb3d6db4a616d883ff51253ce08ac7ec11cb1d208cfaab9e";; \
      *) echo "8e695c5f586a8c53d6c3b01be0b4a422ed218bfed2a56191caebe373a1c18ab2";; \
    esac) && \
    curl -fsSL -o /tmp/delta.tar.gz \
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
    curl -fsSL -o /tmp/eza.tar.gz \
      "https://github.com/eza-community/eza/releases/download/v${EZA_VERSION}/eza_${EZA_ARCH}-unknown-linux-gnu.tar.gz" && \
    echo "${EZA_SHA256}  /tmp/eza.tar.gz" | sha256sum -c - && \
    tar -C /usr/local/bin -xzf /tmp/eza.tar.gz && \
    rm /tmp/eza.tar.gz

# ---------- Headless browser (Chromium + Xvfb + fonts) ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-sandbox \
    xvfb \
    fonts-liberation2 fonts-dejavu-core fonts-noto-core fonts-noto-color-emoji \
    && test -u /usr/lib/chromium/chrome-sandbox \
    && rm -rf /var/lib/apt/lists/*

# ---------- Playwright (Python, uses system Chromium via env vars) ----------
RUN pip install --no-cache-dir --break-system-packages playwright==1.61.0

# Trixie's packaging and wheel modules are dpkg-owned and have no pip RECORD.
# Install the audited releases into /usr/local without removing Debian files.
RUN pip install --no-cache-dir --break-system-packages --ignore-installed \
    packaging==26.2 wheel==0.47.0

RUN pip install --no-cache-dir --break-system-packages \
    requests==2.34.2 httpx==0.28.1 beautifulsoup4==4.15.0 lxml==6.1.1 \
    Pillow==12.3.0 openpyxl==3.1.5 python-docx==1.2.0 \
    pandas==3.0.3 numpy==${NUMPY_VERSION} matplotlib==3.11.1 seaborn==0.13.2 \
    rich==15.0.0 click==8.4.2 tqdm==4.69.0 apprise==1.12.0 \
    jinja2==3.1.6 pyyaml==6.0.3 python-dotenv==1.2.2 markdown==3.10.2 \
    fastapi==0.139.2 uvicorn==0.51.0

# Replace Debian's vulnerable wheel metadata after installing fixed copies in
# /usr/local. pip remains available from the exact PyPI package.
RUN python3 -m pip install --no-cache-dir --break-system-packages --ignore-installed \
      "pip==${PIP_VERSION}" && \
    apt-get purge -y python3-pip python3-wheel && \
    rm -rf /var/lib/apt/lists/* && \
    python3 -m pip --version | grep -F "pip ${PIP_VERSION}" && \
    python3 -m pip check

RUN rm -f /usr/local/bin/dotenv

# npm 12 blocks dependency lifecycle scripts unless they are explicitly reviewed.
# Allow only the exact OpenCode, Claude, and architecture-specific embedded
# PostgreSQL scripts required at runtime; validate every allowed and blocked pin.
COPY config/npm-global-script-policy.json /usr/local/share/holycode/npm-global-script-policy.json
COPY scripts/validate_npm_script_policy.py /usr/local/bin/validate-npm-script-policy
RUN chmod +x /usr/local/bin/validate-npm-script-policy && \
    npm install -g --ignore-scripts "npm@${NPM_VERSION}" && \
    test "$(npm --version)" = "${NPM_VERSION}"

# ---------- OpenCode (AI coding agent) ----------
# Installed via npm as root (global install needs write access to /usr/local/lib)
RUN npm i -g --ignore-scripts "opencode-ai@${OPENCODE_VERSION}" "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}" && \
    rm -rf /root/.npm
ENV PATH="/home/opencode/.local/bin:${PATH}"

# Drizzle Kit's stable release still declares an unused legacy loader and older
# nested esbuild; remove both in the install layer and use the audited global pin.
RUN npm i -g --ignore-scripts \
    "typescript@${TYPESCRIPT_VERSION}" "tsx@${TSX_VERSION}" \
    "pnpm@${PNPM_VERSION}" \
    "vite@${VITE_VERSION}" esbuild@0.28.1 \
    eslint@10.7.0 "prettier@${PRETTIER_VERSION}" \
    serve@14.2.6 nodemon@3.1.14 \
    dotenv-cli@11.0.0 \
    "wrangler@${WRANGLER_VERSION}" \
    pm2@7.0.3 \
    "prisma@${PRISMA_VERSION}" drizzle-kit@0.31.10 \
    "lighthouse@${LIGHTHOUSE_VERSION}" \
    json-server@0.17.4 http-server@14.1.1 && \
    DRIZZLE_DIR=/usr/local/lib/node_modules/drizzle-kit && \
    jq '.dependencies |= del(."@esbuild-kit/esm-loader") | .dependencies.esbuild = "0.28.1"' \
      "$DRIZZLE_DIR/package.json" > "$DRIZZLE_DIR/package.json.tmp" && \
    mv "$DRIZZLE_DIR/package.json.tmp" "$DRIZZLE_DIR/package.json" && \
    rm -rf \
      "$DRIZZLE_DIR/node_modules/@esbuild-kit" \
      "$DRIZZLE_DIR/node_modules/@esbuild" \
      "$DRIZZLE_DIR/node_modules/esbuild" && \
    ln -s ../../esbuild "$DRIZZLE_DIR/node_modules/esbuild" && \
    test "$(node -p 'require("/usr/local/lib/node_modules/drizzle-kit/node_modules/esbuild/package.json").version')" = "0.28.1" && \
    drizzle-kit --version && \
    drizzle-kit --help >/dev/null && \
    rm -rf /root/.npm

# Netlify's optional platform package still contains stale local-functions-proxy
# binaries. Keep remote build/deploy commands and remove the unsupported local runtime.
RUN npm i -g --ignore-scripts --omit=optional "netlify-cli@${NETLIFY_CLI_VERSION}" && \
    rm -rf /usr/local/lib/node_modules/netlify-cli/node_modules/@netlify/local-functions-proxy-* && \
    rm -f /usr/local/lib/node_modules/netlify-cli/node_modules/.bin/local-functions-proxy && \
    test -z "$(find /usr/local/lib/node_modules/netlify-cli -path '*/@netlify/local-functions-proxy-*/bin/local-functions-proxy' -print -quit)" && \
    netlify --version | grep -F "netlify-cli/${NETLIFY_CLI_VERSION}" && \
    netlify build --help >/dev/null && \
    netlify deploy --help >/dev/null && \
    rm -rf /root/.npm

RUN npm i -g --ignore-scripts \
    "paperclipai@${PAPERCLIP_VERSION}" && \
    rm -rf /root/.npm
# Paperclip's Cursor adapter currently resolves Undici 5 through Connect 1.x.
# Keep Paperclip stable while replacing that HTTP client with the first fixed
# 6.x release; remove this reviewed compatibility patch when Paperclip updates Connect.
RUN test "$(npm view "undici@${PAPERCLIP_UNDICI_VERSION}" dist.integrity)" = \
      "sha512-YmfV3YnEDzXRC5lZ2jWtWWHKGUm1zIt8AhesR1tens+HTNv+YZlN/dp6G727LOvMJ8xjP9Be7Y2Sdr96LDm+pg==" && \
    UNDICI_TARBALL=$(npm pack --silent --pack-destination /tmp "undici@${PAPERCLIP_UNDICI_VERSION}") && \
    UNDICI_DIR=/usr/local/lib/node_modules/paperclipai/node_modules/undici && \
    CONNECT_NODE_PACKAGE=/usr/local/lib/node_modules/paperclipai/node_modules/@connectrpc/connect-node/package.json && \
    rm -rf "$UNDICI_DIR" && mkdir "$UNDICI_DIR" && \
    tar -xzf "/tmp/${UNDICI_TARBALL}" -C "$UNDICI_DIR" --strip-components=1 && \
    rm "/tmp/${UNDICI_TARBALL}" && \
    node -e 'const fs=require("fs"); const file=process.argv[1]; const version=process.argv[2]; const pkg=JSON.parse(fs.readFileSync(file,"utf8")); pkg.dependencies.undici=version; fs.writeFileSync(file,`${JSON.stringify(pkg,null,2)}\n`)' \
      "$CONNECT_NODE_PACKAGE" "^${PAPERCLIP_UNDICI_VERSION}" && \
    test "$(node -p 'require("/usr/local/lib/node_modules/paperclipai/node_modules/undici/package.json").version')" = \
      "${PAPERCLIP_UNDICI_VERSION}" && \
    (cd /usr/local/lib/node_modules/paperclipai && npm ls undici --all >/dev/null) && \
    node --input-type=module -e 'const {testEnvironment}=await import("file:///usr/local/lib/node_modules/paperclipai/node_modules/@paperclipai/adapter-cursor-cloud/dist/server/index.js"); const result=await testEnvironment({adapterType:"cursor_cloud",config:{}}); if(result.status!=="fail" || !result.checks.some((check)=>check.code==="cursor_cloud_api_key_missing")) process.exit(1)'
RUN find /usr/local/lib/node_modules/paperclipai/node_modules/@embedded-postgres \
      -path '*/native/lib' -type d -exec sh -c '\
        for lib_dir do \
          [ -f "$lib_dir/libcrypto.so.1.1" ] && ln -sf libcrypto.so.1.1 "$lib_dir/libcrypto.so.1"; \
          [ -f "$lib_dir/libssl.so.1.1" ] && ln -sf libssl.so.1.1 "$lib_dir/libssl.so.1"; \
        done' sh {} +
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
    esbuild --version | grep -Fx "0.28.1" && \
    prisma --version >/dev/null && \
    wrangler --version | grep -F "${WRANGLER_VERSION}" && \
    ! command -v vercel && ! command -v sharp && ! command -v concurrently && ! command -v lhci && \
    WORKERD_BIN=$(find /usr/local/lib/node_modules/wrangler -path '*/workerd/bin/workerd' -type f -print -quit) && \
    test -n "${WORKERD_BIN}" && "${WORKERD_BIN}" --version >/dev/null && \
    node -e 'const ssh2=require("/usr/local/lib/node_modules/paperclipai/node_modules/ssh2"); if(typeof ssh2.Client!=="function") process.exit(1)'

RUN mkdir -p /usr/local/share/holycode && \
    dpkg-query -W -f='${binary:Package}\t${Version}\n' | sort > /usr/local/share/holycode/dpkg-inventory.txt

# ---------- Copy config files ----------
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY scripts/bootstrap.sh /usr/local/bin/bootstrap.sh
COPY config/opencode.json /usr/local/share/holycode/opencode.json
COPY config/skills /usr/local/share/holycode/skills
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/bootstrap.sh

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
