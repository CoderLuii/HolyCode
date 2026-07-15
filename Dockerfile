# ==============================================================================
# HolyCode - Pre-configured Docker Environment for OpenCode
# https://github.com/coderluii/holycode
# ==============================================================================

FROM node:24.18.0-bookworm-slim@sha256:6f7b03f7c2c8e2e784dcf9295400527b9b1270fd37b7e9a7285cf83b6951452d

# ---------- Build args ----------
ARG S6_OVERLAY_VERSION=3.2.3.1
ARG FZF_VERSION=0.74.0
ARG LAZYGIT_VERSION=0.63.0
ARG DELTA_VERSION=0.19.2
ARG EZA_VERSION=0.23.5
ARG HERMES_AGENT_VERSION=v2026.7.7.2
ARG HERMES_AGENT_REF=b7751df34688835a108e0d630f3495fc11f3df79
# renovate: datasource=npm depName=opencode-ai
ARG OPENCODE_VERSION=1.18.1
# renovate: datasource=npm depName=@anthropic-ai/claude-code
ARG CLAUDE_CODE_VERSION=2.1.210
# renovate: datasource=npm depName=paperclipai
ARG PAPERCLIP_VERSION=2026.707.0
# renovate: datasource=npm depName=typescript
ARG TYPESCRIPT_VERSION=6.0.3
# renovate: datasource=npm depName=tsx
ARG TSX_VERSION=4.23.1
# renovate: datasource=npm depName=pnpm
ARG PNPM_VERSION=11.13.0
# renovate: datasource=npm depName=wrangler
ARG WRANGLER_VERSION=4.110.0
# renovate: datasource=npm depName=vercel
ARG VERCEL_VERSION=54.21.0
# renovate: datasource=npm depName=netlify-cli
ARG NETLIFY_CLI_VERSION=26.2.0
# renovate: datasource=pypi depName=numpy
ARG NUMPY_VERSION=2.4.6
ARG TARGETARCH

LABEL org.opencontainers.image.source=https://github.com/CoderLuii/HolyCode \
    io.holycode.version.opencode=${OPENCODE_VERSION} \
    io.holycode.version.claude-code=${CLAUDE_CODE_VERSION} \
    io.holycode.version.paperclip=${PAPERCLIP_VERSION} \
    io.holycode.version.typescript=${TYPESCRIPT_VERSION} \
    io.holycode.version.tsx=${TSX_VERSION} \
    io.holycode.version.pnpm=${PNPM_VERSION} \
    io.holycode.version.wrangler=${WRANGLER_VERSION} \
    io.holycode.version.vercel=${VERCEL_VERSION} \
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
    CHROMIUM_FLAGS="--no-sandbox --disable-gpu --disable-dev-shm-usage" \
    OPENCODE_DISABLE_AUTOUPDATE=true \
    OPENCODE_DISABLE_TERMINAL_TITLE=true

# ---------- s6-overlay v3 (multi-arch) ----------
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends xz-utils curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*
RUN S6_ARCH=$(case "$TARGETARCH" in arm64) echo "aarch64";; *) echo "x86_64";; esac) && \
    S6_ARCH_SHA256=$(case "$TARGETARCH" in \
      arm64) echo "c79b5cc7e5e405f6e1ae1466a8160ac84d29b86614e1e01ff0fb11dc832fee1b";; \
      *) echo "ed72fdb3abf196472d121b026bed63b46f3443507bd2ce67df6bd187f7d4dc0a";; \
    esac) && \
    curl -fsSL -o /tmp/s6-overlay-noarch.tar.xz \
      "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz" && \
    curl -fsSL -o /tmp/s6-overlay-arch.tar.xz \
      "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${S6_ARCH}.tar.xz" && \
    echo "43d99d266fefe32cdc1510963aaadeb211cc8450b60af27817b64af450c934be  /tmp/s6-overlay-noarch.tar.xz" | sha256sum -c - && \
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
    postgresql-client redis-tools sqlite3 \
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
      arm64) echo "bd9e6165ebdb702215d42368cbb95b8dd70a4e77ee97925adac8c31660e30ef7";; \
      *) echo "cf919f05b7581b4c744d764eaa704665d61dd6d3ca785f0df2351281dff60cda";; \
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
RUN curl -fsSL -o /tmp/githubcli-archive-keyring.gpg \
      https://cli.github.com/packages/githubcli-archive-keyring.gpg && \
    echo "6084d5d7bd8e288441e0e94fc6275570895da18e6751f70f057485dc2d1a811b  /tmp/githubcli-archive-keyring.gpg" | sha256sum -c - && \
    install -m 0644 /tmp/githubcli-archive-keyring.gpg /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    rm /tmp/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      > /etc/apt/sources.list.d/github-cli.list && \
    apt-get update && apt-get install -y gh && rm -rf /var/lib/apt/lists/*

# ---------- lazygit ----------
RUN LAZYGIT_ARCH=$(case "$TARGETARCH" in arm64) echo "arm64";; *) echo "x86_64";; esac) && \
    LAZYGIT_SHA256=$(case "$TARGETARCH" in \
      arm64) echo "aac147abf5ce43afe6ae8bcb14b0d479111975a189302d7a99386deca70d57f7";; \
      *) echo "cf5cfa3e116d7775f3600a51ec1d9ce7ba554a08b9566c7c2da83cb0023efabf";; \
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
    chromium \
    xvfb \
    fonts-liberation2 fonts-dejavu-core fonts-noto-core fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# ---------- Playwright (Python, uses system Chromium via env vars) ----------
RUN pip install --no-cache-dir --break-system-packages playwright==1.61.0

RUN pip install --no-cache-dir --break-system-packages \
    requests==2.33.0 httpx==0.28.1 beautifulsoup4==4.15.0 lxml==6.1.1 \
    Pillow==12.2.0 openpyxl==3.1.5 python-docx==1.2.0 \
    pandas==3.0.3 numpy==${NUMPY_VERSION} matplotlib==3.11.0 seaborn==0.13.2 \
    rich==14.3.3 click==8.4.2 tqdm==4.68.4 apprise==1.12.0 \
    jinja2==3.1.6 pyyaml==6.0.3 python-dotenv==1.2.2 markdown==3.10.2 \
    fastapi==0.139.0 uvicorn==0.51.0

RUN rm -f /usr/local/bin/dotenv

# ---------- OpenCode (AI coding agent) ----------
# Installed via npm as root (global install needs write access to /usr/local/lib)
RUN npm i -g "opencode-ai@${OPENCODE_VERSION}" "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}" && \
    rm -rf /root/.npm
ENV PATH="/home/opencode/.local/bin:${PATH}"

# Drizzle Kit's stable release still declares an unused legacy loader and older
# nested esbuild; remove both in the install layer and use the audited global pin.
RUN npm i -g \
    "typescript@${TYPESCRIPT_VERSION}" "tsx@${TSX_VERSION}" \
    "pnpm@${PNPM_VERSION}" \
    vite@8.1.4 esbuild@0.28.1 \
    eslint@10.7.0 prettier@3.9.5 \
    serve@14.2.6 nodemon@3.1.14 concurrently@10.0.3 \
    dotenv-cli@11.0.0 \
    "wrangler@${WRANGLER_VERSION}" "vercel@${VERCEL_VERSION}" \
    pm2@7.0.3 \
    prisma@7.8.0 drizzle-kit@0.31.10 \
    lighthouse@13.4.0 @lhci/cli@0.15.1 \
    sharp-cli@5.2.0 json-server@0.17.4 http-server@14.1.1 && \
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
RUN npm i -g --omit=optional "netlify-cli@${NETLIFY_CLI_VERSION}" && \
    rm -rf /usr/local/lib/node_modules/netlify-cli/node_modules/@netlify/local-functions-proxy-* && \
    rm -f /usr/local/lib/node_modules/netlify-cli/node_modules/.bin/local-functions-proxy && \
    test -z "$(find /usr/local/lib/node_modules/netlify-cli -path '*/@netlify/local-functions-proxy-*/bin/local-functions-proxy' -print -quit)" && \
    netlify --version | grep -F "netlify-cli/${NETLIFY_CLI_VERSION}" && \
    netlify build --help >/dev/null && \
    netlify deploy --help >/dev/null && \
    rm -rf /root/.npm

RUN HERMES_AGENT_COMMIT=$(git ls-remote --tags https://github.com/NousResearch/hermes-agent.git "refs/tags/${HERMES_AGENT_VERSION}" | awk '{print $1}') && \
    if [ "$HERMES_AGENT_COMMIT" != "$HERMES_AGENT_REF" ]; then \
      echo "Hermes tag ${HERMES_AGENT_VERSION} resolved to ${HERMES_AGENT_COMMIT:-missing}, expected ${HERMES_AGENT_REF}" >&2; \
      exit 1; \
    fi && \
    pip install --no-cache-dir --break-system-packages \
    "hermes-agent[pty,mcp,messaging] @ git+https://github.com/NousResearch/hermes-agent.git@${HERMES_AGENT_REF}" && \
    python3 -m pip check

RUN npm i -g "paperclipai@${PAPERCLIP_VERSION}" && \
    rm -rf /root/.npm
RUN find /usr/local/lib/node_modules/paperclipai/node_modules/@embedded-postgres \
      -path '*/native/lib' -type d -exec sh -c '\
        for lib_dir do \
          [ -f "$lib_dir/libcrypto.so.1.1" ] && ln -sf libcrypto.so.1.1 "$lib_dir/libcrypto.so.1"; \
          [ -f "$lib_dir/libssl.so.1.1" ] && ln -sf libssl.so.1.1 "$lib_dir/libssl.so.1"; \
        done' sh {} +

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

COPY s6-overlay/s6-rc.d/hermes/type /etc/s6-overlay/s6-rc.d/hermes/type
COPY s6-overlay/s6-rc.d/hermes/run /etc/s6-overlay/s6-rc.d/hermes/run
COPY s6-overlay/s6-rc.d/paperclip/type /etc/s6-overlay/s6-rc.d/paperclip/type
COPY s6-overlay/s6-rc.d/paperclip/run /etc/s6-overlay/s6-rc.d/paperclip/run
RUN chmod +x /etc/s6-overlay/s6-rc.d/hermes/run /etc/s6-overlay/s6-rc.d/paperclip/run

# ---------- Working directory ----------
WORKDIR /workspace

# ---------- Expose web UI port ----------
EXPOSE 4096

# ---------- Health check ----------
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -sf http://localhost:4096/ || exit 1

# ---------- s6-overlay as PID 1 ----------
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
