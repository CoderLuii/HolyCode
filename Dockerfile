# ==============================================================================
# HolyCode - Pre-configured Docker Environment for OpenCode
# https://github.com/coderluii/holycode
# ==============================================================================

# renovate: datasource=github-releases depName=cli/cli
ARG GITHUB_CLI_VERSION=2.102.0
# renovate: datasource=github-releases depName=junegunn/fzf
ARG FZF_VERSION=0.74.4
# renovate: datasource=github-releases depName=jesseduffield/lazygit
ARG LAZYGIT_VERSION=0.66.0

FROM node:24.21.0-trixie-slim@sha256:8ec5d7557396cfe32d21c3f9c13072355ceab22b584578ca4bb28af31120cffe

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
ARG OPENCODE_VERSION=1.18.34
# renovate: datasource=npm depName=@anthropic-ai/claude-code
ARG CLAUDE_CODE_VERSION=2.1.290
# renovate: datasource=npm depName=paperclipai
ARG PAPERCLIP_VERSION=2026.831.1
# renovate: datasource=npm depName=@cursor/sdk
ARG PAPERCLIP_CURSOR_SDK_VERSION=1.0.36
# renovate: datasource=npm depName=jsdom
ARG PAPERCLIP_JSDOM_VERSION=30.1.2
# renovate: datasource=npm depName=@fission-ai/openspec
ARG OPENSPEC_VERSION=1.14.1
# renovate: datasource=npm depName=undici
ARG PAPERCLIP_UNDICI_VERSION=8.11.2
# renovate: datasource=npm depName=opencode-claude-auth
ARG CLAUDE_AUTH_PLUGIN_VERSION=2.2.1
# renovate: datasource=npm depName=typescript
ARG TYPESCRIPT_VERSION=6.0.3
# renovate: datasource=npm depName=npm
ARG NPM_VERSION=12.2.0
# renovate: datasource=npm depName=brace-expansion
ARG NPM_BRACE_EXPANSION_VERSION=5.0.12
# renovate: datasource=npm depName=tar
ARG NPM_TAR_VERSION=7.5.22
# renovate: datasource=npm depName=ip-address
ARG NPM_IP_ADDRESS_VERSION=10.7.2
# renovate: datasource=npm depName=node-gyp
ARG NPM_NODE_GYP_VERSION=13.0.2
# renovate: datasource=npm depName=undici
ARG NPM_NODE_GYP_UNDICI_VERSION=8.11.2
# renovate: datasource=npm depName=js-yaml
ARG PM2_JS_YAML_VERSION=4.3.2
# renovate: datasource=npm depName=basic-ftp
ARG PM2_BASIC_FTP_VERSION=6.2.1
# renovate: datasource=npm depName=tsx
ARG TSX_VERSION=4.23.15
# renovate: datasource=npm depName=pnpm
ARG PNPM_VERSION=12.9.1
# renovate: datasource=npm depName=vite
ARG VITE_VERSION=8.3.2
# renovate: datasource=npm depName=prettier
ARG PRETTIER_VERSION=3.9.9
# renovate: datasource=npm depName=prisma
ARG PRISMA_VERSION=7.10.0
# renovate: datasource=npm depName=deepmerge-ts
ARG PRISMA_DEEPMERGE_VERSION=8.0.2
# renovate: datasource=npm depName=mysql2
ARG PRISMA_MYSQL2_VERSION=3.24.5
# renovate: datasource=npm depName=@types/node
ARG PRISMA_TYPES_NODE_VERSION=20.19.43
# renovate: datasource=npm depName=undici-types
ARG PRISMA_UNDICI_TYPES_VERSION=6.21.0
# renovate: datasource=npm depName=lighthouse
ARG LIGHTHOUSE_VERSION=13.5.0
# renovate: datasource=npm depName=wrangler
ARG WRANGLER_VERSION=4.147.0
# renovate: datasource=npm depName=miniflare
ARG WRANGLER_MINIFLARE_VERSION=5.20261001.0-alpha
# renovate: datasource=npm depName=sharp
ARG WRANGLER_SHARP_VERSION=0.35.4
# renovate: datasource=npm depName=@img/sharp-libvips-linux-x64
ARG WRANGLER_SHARP_LIBVIPS_VERSION=1.3.3
# renovate: datasource=npm depName=eslint
ARG ESLINT_VERSION=10.12.0
# renovate: datasource=pypi depName=numpy
ARG NUMPY_VERSION=2.5.3
# renovate: datasource=pypi depName=pip
ARG PIP_VERSION=26.2.1
# renovate: datasource=pypi depName=msgpack
ARG PIP_VENDOR_MSGPACK_VERSION=1.2.2
ARG PIP_VENDOR_MSGPACK_SHA256=9eb0b0e602064527a045ea28c4f174ed69383587e29cebe28947e3b84106eb2a
# pip 26.2.1 vendors pkg_resources from vulnerable setuptools 70.3.0.
ARG PIP_VENDOR_PKG_RESOURCES_VERSION=78.1.1
ARG PIP_VENDOR_PKG_RESOURCES_SHA256=fcc17fd9cd898242f6b4adfaca46137a9edef687f43e6f78469692a5e70d851d
# renovate: datasource=pypi depName=urllib3
ARG PIP_VENDOR_URLLIB3_VERSION=2.8.0
ARG PIP_VENDOR_URLLIB3_WHEEL_SHA256=0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3
ARG PIP_VENDOR_URLLIB3_ARCHIVE_SHA256=c64eb33b95a5cbd0afd35cadfb3778da6e7c979efa634312f39a392ca3cb11f2
# renovate: datasource=pypi depName=setuptools
ARG SETUPTOOLS_VERSION=84.0.0
ARG RELEASE_APT_REFRESH=2026-10-05
ARG RELEASE_VERSION=v1.2.5
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
    io.holycode.version.npm-brace-expansion=${NPM_BRACE_EXPANSION_VERSION} \
    io.holycode.version.npm-tar=${NPM_TAR_VERSION} \
    io.holycode.version.npm-ip-address=${NPM_IP_ADDRESS_VERSION} \
    io.holycode.version.npm-node-gyp=${NPM_NODE_GYP_VERSION} \
    io.holycode.version.npm-node-gyp-undici=${NPM_NODE_GYP_UNDICI_VERSION} \
    io.holycode.version.pm2-js-yaml=${PM2_JS_YAML_VERSION} \
    io.holycode.version.pm2-basic-ftp=${PM2_BASIC_FTP_VERSION} \
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
    io.holycode.version.prisma-types-node=${PRISMA_TYPES_NODE_VERSION} \
    io.holycode.version.prisma-undici-types=${PRISMA_UNDICI_TYPES_VERSION} \
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
      arm64) echo "5d673b849f494f0d64ec471d8640b153ca8849e3846a31da17abdcfce8df6b46";; \
      *) echo "05e6813a337cc722c3ed07e54a764b75cc5d671e2e60459db0ba696ee5fa7504";; \
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
      arm64) echo "7862c86c72f43df3a2d93ddde6f473285b4e2af61b494849846827e513ef6484";; \
      *) echo "bb766f710eef8ede859c18578c72c327597cd4c8a85b06001b1f3843c6019386";; \
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
      arm64) echo "9a4fc4656897ac9f7877b835473ce1a75620cc267f554c57fc4ff266407f3257";; \
      *) echo "5b45541155d20bd32bf2cc5ab5b7e3d91c2eebf0fb1242281350edc27d59d2b7";; \
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
COPY patches/pip-vendored-pkg-resources-78.1.1.patch /tmp/pip-vendored-pkg-resources.patch
COPY patches/pip-vendored-urllib3-2.8.0.tar.gz /tmp/pip-vendored-urllib3-2.8.0.tar.gz
COPY patches/pip-vendored-bom-26.2.1-urllib3-2.8.0.cdx.json /tmp/pip-vendored-bom.cdx.json
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
    curl --disable --retry 8 --retry-all-errors --retry-max-time 300 --remove-on-error --connect-timeout 15 --max-time 300 -fsSL -o /tmp/msgpack.tar.gz \
      "https://files.pythonhosted.org/packages/6d/44/ea2100ec54d30c46ee9dba10a3bfb79b655e96c6df237238a3234c75869b/msgpack-${PIP_VENDOR_MSGPACK_VERSION}.tar.gz" && \
    echo "${PIP_VENDOR_MSGPACK_SHA256}  /tmp/msgpack.tar.gz" | sha256sum -c - && \
    curl --disable --retry 8 --retry-all-errors --retry-max-time 300 --remove-on-error --connect-timeout 15 --max-time 300 -fsSL -o /tmp/setuptools.tar.gz \
      "https://files.pythonhosted.org/packages/81/9c/42314ee079a3e9c24b27515f9fbc7a3c1d29992c33451779011c74488375/setuptools-${PIP_VENDOR_PKG_RESOURCES_VERSION}.tar.gz" && \
    echo "${PIP_VENDOR_PKG_RESOURCES_SHA256}  /tmp/setuptools.tar.gz" | sha256sum -c - && \
    curl --disable --retry 8 --retry-all-errors --retry-max-time 300 --remove-on-error --connect-timeout 15 --max-time 300 -fsSL -o /tmp/urllib3.whl \
      "https://files.pythonhosted.org/packages/92/9d/c4e665119135114480843e7ab388fa94d8480650450e6f8e26b70d323a4c/urllib3-${PIP_VENDOR_URLLIB3_VERSION}-py3-none-any.whl" && \
    echo "${PIP_VENDOR_URLLIB3_WHEEL_SHA256}  /tmp/urllib3.whl" | sha256sum -c - && \
    echo "${PIP_VENDOR_URLLIB3_ARCHIVE_SHA256}  /tmp/pip-vendored-urllib3-2.8.0.tar.gz" | sha256sum -c - && \
    echo "4e645472781870c87c896be33c1c3e0f93b2f8efeaf8ef780f629cad7d960e75  /tmp/pip-vendored-bom.cdx.json" | sha256sum -c - && \
    mkdir -p /tmp/msgpack /tmp/setuptools && \
    tar -xzf /tmp/msgpack.tar.gz -C /tmp/msgpack --strip-components=1 && \
    tar -xzf /tmp/setuptools.tar.gz -C /tmp/setuptools --strip-components=1 && \
    (cd /tmp/setuptools && patch -p1 < /tmp/pip-vendored-pkg-resources.patch) && \
    PIP_VENDOR_DIR="$(python3 -c 'import pathlib,pip._vendor; print(pathlib.Path(pip._vendor.__file__).parent)')" && \
    rm -rf "$PIP_VENDOR_DIR/msgpack" "$PIP_VENDOR_DIR/pkg_resources" "$PIP_VENDOR_DIR/urllib3" && \
    cp -a /tmp/msgpack/msgpack "$PIP_VENDOR_DIR/msgpack" && \
    cp -a /tmp/setuptools/pkg_resources "$PIP_VENDOR_DIR/pkg_resources" && \
    tar -xzf /tmp/pip-vendored-urllib3-2.8.0.tar.gz -C "$PIP_VENDOR_DIR" && \
    cp /tmp/msgpack/COPYING "$PIP_VENDOR_DIR/msgpack/COPYING" && \
    cp /tmp/setuptools/LICENSE "$PIP_VENDOR_DIR/pkg_resources/LICENSE" && \
    cp /tmp/pip-vendored-bom.cdx.json "$PIP_VENDOR_DIR/bom.cdx.json" && \
    python3 -c 'import pathlib,sys,zipfile; archive=zipfile.ZipFile(sys.argv[1]); wheel_license=archive.read("urllib3-2.8.0.dist-info/licenses/LICENSE.txt"); vendored_license=pathlib.Path(sys.argv[2]).read_bytes(); assert wheel_license==vendored_license' \
      /tmp/urllib3.whl "$PIP_VENDOR_DIR/urllib3/LICENSE.txt" && \
    rm -rf "$PIP_VENDOR_DIR/pkg_resources/tests" "$PIP_VENDOR_DIR/pkg_resources/api_tests.txt" && \
    sed -i \
      "s/^msgpack==.*/msgpack==${PIP_VENDOR_MSGPACK_VERSION}/; s/^setuptools==.*/setuptools==${PIP_VENDOR_PKG_RESOURCES_VERSION}/; s/urllib3==.*/urllib3==${PIP_VENDOR_URLLIB3_VERSION}/" \
      "$PIP_VENDOR_DIR/vendor.txt" && \
    python3 -c 'import functools,json,pathlib,sys; path=pathlib.Path(sys.argv[1]); text=path.read_text(); versions={"msgpack":("1.1.2",sys.argv[2]),"setuptools":("70.3.0",sys.argv[3])}; replacements={"pkg:pypi/{0}@{1}".format(name,old):"pkg:pypi/{0}@{1}".format(name,new) for name,(old,new) in versions.items()}; assert all(old in text for old in replacements); assert "pkg:pypi/urllib3@2.8.0" in text and "pkg:pypi/urllib3@2.7.0" not in text; data=json.loads(functools.reduce(lambda value,pair:value.replace(*pair),replacements.items(),text)); [(component.update(version=versions[component["name"]][1]) if component.get("name") in versions else None) for component in data.get("components",[])]; path.write_text(json.dumps(data,indent=2)+"\n")' \
      "$PIP_VENDOR_DIR/bom.cdx.json" "$PIP_VENDOR_MSGPACK_VERSION" "$PIP_VENDOR_PKG_RESOURCES_VERSION" && \
    PIP_DIST_INFO="/usr/local/lib/python3.13/dist-packages/pip-${PIP_VERSION}.dist-info" && \
    install -m 0644 "$PIP_VENDOR_DIR/msgpack/COPYING" "$PIP_DIST_INFO/licenses/src/pip/_vendor/msgpack/COPYING" && \
    install -m 0644 "$PIP_VENDOR_DIR/pkg_resources/LICENSE" "$PIP_DIST_INFO/licenses/src/pip/_vendor/pkg_resources/LICENSE" && \
    install -m 0644 "$PIP_VENDOR_DIR/urllib3/LICENSE.txt" "$PIP_DIST_INFO/licenses/src/pip/_vendor/urllib3/LICENSE.txt" && \
    python3 /tmp/verify-pip-vendor-record.py --refresh && \
    rm -rf /tmp/msgpack /tmp/setuptools /tmp/msgpack.tar.gz /tmp/setuptools.tar.gz \
      /tmp/pip-vendored-pkg-resources.patch /tmp/pip-vendored-urllib3-2.8.0.tar.gz \
      /tmp/urllib3.whl /tmp/pip-vendored-bom.cdx.json /tmp/verify-pip-vendor-record.py && \
    rm -rf /var/lib/apt/lists/* && \
    python3 -m pip --version | grep -F "pip ${PIP_VERSION}" && \
    python3 -c 'import pip._vendor.msgpack as msgpack; import pip._vendor.urllib3 as urllib3; assert msgpack.__version__ == "1.2.2"; assert urllib3.__version__ == "2.8.0"; assert msgpack.unpackb(msgpack.packb({"holycode": True})) == {"holycode": True}; import pip._vendor.pkg_resources' && \
    _PIP_USE_IMPORTLIB_METADATA=0 python3 -m pip list --format=json >/dev/null && \
    python3 -c 'import setuptools; assert setuptools.__version__ == "84.0.0"' && \
    python3 -m pip check && \
    python3 /tmp/test_pip_vendor_urllib3.py && \
    rm /tmp/test_pip_vendor_urllib3.py

RUN rm -f /usr/local/bin/dotenv

RUN npm install -g --ignore-scripts "npm@${NPM_VERSION}" && \
    test "$(npm --version)" = "${NPM_VERSION}" && \
    rm -rf /root/.npm
RUN test "$(npm view "brace-expansion@${NPM_BRACE_EXPANSION_VERSION}" dist.integrity)" = \
      "sha512-YovQ3rzhaLMIrDjNDMkNS01tea93qhEhG5xy8f6+R0l+dw3Ki+5sCoIoI942iuLZTHWogWktgwVDhU09iNEimQ==" && \
    BRACE_TARBALL=$(npm pack --silent --pack-destination /tmp \
      "brace-expansion@${NPM_BRACE_EXPANSION_VERSION}") && \
    BRACE_DIR=/usr/local/lib/node_modules/npm/node_modules/brace-expansion && \
    rm -rf "$BRACE_DIR" && mkdir "$BRACE_DIR" && \
    tar -xzf "/tmp/${BRACE_TARBALL}" -C "$BRACE_DIR" --strip-components=1 && \
    rm "/tmp/${BRACE_TARBALL}" && \
    test "$(node -p 'require("/usr/local/lib/node_modules/npm/node_modules/brace-expansion/package.json").version')" = \
      "${NPM_BRACE_EXPANSION_VERSION}" && \
    (cd /usr/local/lib/node_modules/npm && npm ls brace-expansion --all >/dev/null) && \
    rm -rf /root/.npm
RUN test "$(npm view "tar@${NPM_TAR_VERSION}" dist.integrity)" = \
      "sha512-MFO/QzvtAOmJbkhOaCTvbGcFN9L9b+JunIsDwaKljSOdcLMea3NJ1k9Usz/rjdfSXTq4dfzfeS7W4p4YOAAHeA==" && \
    NPM_TAR_TARBALL=$(npm pack --silent --pack-destination /tmp "tar@${NPM_TAR_VERSION}") && \
    NPM_TAR_DIR=/usr/local/lib/node_modules/npm/node_modules/tar && \
    rm -rf "$NPM_TAR_DIR" && mkdir "$NPM_TAR_DIR" && \
    tar -xzf "/tmp/${NPM_TAR_TARBALL}" -C "$NPM_TAR_DIR" --strip-components=1 && \
    rm "/tmp/${NPM_TAR_TARBALL}" && \
    test "$(node -p 'require("/usr/local/lib/node_modules/npm/node_modules/tar/package.json").version')" = \
      "${NPM_TAR_VERSION}" && \
    (cd /usr/local/lib/node_modules/npm && npm ls tar --all >/dev/null) && \
    rm -rf /root/.npm
# npm 12.2.0 resolves ip-address through socks. Keep the compatible
# socks range and replace that nested copy with the fixed 10.7.2 release.
RUN test "$(npm view "ip-address@${NPM_IP_ADDRESS_VERSION}" dist.integrity)" = \
      "sha512-7H/2gFSIitxc0hG3nOI1glS8QLo/EHBFFLk8vEUjXY/xu0AdL8jZ9U1IzO2PUm0d2D/ofQcAifb0g6OBkt8U7w==" && \
    NPM_IP_ADDRESS_TARBALL=$(npm pack --silent --pack-destination /tmp \
      "ip-address@${NPM_IP_ADDRESS_VERSION}") && \
    NPM_IP_ADDRESS_DIR=/usr/local/lib/node_modules/npm/node_modules/ip-address && \
    NPM_SOCKS_PACKAGE=/usr/local/lib/node_modules/npm/node_modules/socks/package.json && \
    node -e 'const pkg=require(process.argv[1]); if(pkg.version!=="2.8.9" || pkg.dependencies["ip-address"]!=="^10.1.1") process.exit(1)' \
      "$NPM_SOCKS_PACKAGE" && \
    rm -rf "$NPM_IP_ADDRESS_DIR" && mkdir "$NPM_IP_ADDRESS_DIR" && \
    tar -xzf "/tmp/${NPM_IP_ADDRESS_TARBALL}" -C "$NPM_IP_ADDRESS_DIR" --strip-components=1 && \
    rm "/tmp/${NPM_IP_ADDRESS_TARBALL}" && \
    test "$(node -p 'require("/usr/local/lib/node_modules/npm/node_modules/ip-address/package.json").version')" = \
      "${NPM_IP_ADDRESS_VERSION}" && \
    (cd /usr/local/lib/node_modules/npm && npm ls ip-address --all >/dev/null) && \
    test "$(npm prefix -g)" = "/usr/local" && \
    rm -rf /root/.npm
# npm 12.2.0 bundles node-gyp 13.0.0 with Undici 6.28.0. Its declared
# compatible node-gyp 13.0.2 release consumes the patched Undici 8 line.
COPY scripts/test_node_gyp_download.mjs /tmp/test_node_gyp_download.mjs
COPY scripts/test_node_gyp_native.mjs /tmp/test_node_gyp_native.mjs
RUN NPM_NODE_GYP_INTEGRITY="sha512-SXTvw3PxznpowYhJSOD9mVQBgDaCTWXffX+wQZsQ7PbcTV86TsXCUcSZhHnskFQvrvn/OdSzJPMsptT2pIj9ww==" && \
    NPM_NODE_GYP_UNDICI_INTEGRITY="sha512-u4UB2/IrKdU6lFxumHmmo1a3fCQO5tzQllRorfoRS63txhrB7xTpSn1PftwC4qEHkOaqP95fCWW4lJzwErwzhQ==" && \
    test "$(npm view "node-gyp@${NPM_NODE_GYP_VERSION}" dist.integrity)" = "$NPM_NODE_GYP_INTEGRITY" && \
    test "$(npm view "undici@${NPM_NODE_GYP_UNDICI_VERSION}" dist.integrity)" = "$NPM_NODE_GYP_UNDICI_INTEGRITY" && \
    NPM_PACKAGE=/usr/local/lib/node_modules/npm/package.json && \
    NPM_NODE_GYP_DIR=/usr/local/lib/node_modules/npm/node_modules/node-gyp && \
    NPM_NODE_GYP_UNDICI_DIR=/usr/local/lib/node_modules/npm/node_modules/undici && \
    node -e 'const npm=require(process.argv[1]); const gyp=require(process.argv[2]); if(npm.version!=="12.2.0" || npm.dependencies["node-gyp"]!=="^13.0.0" || gyp.version!=="13.0.0" || gyp.dependencies.undici!=="^6.25.0") process.exit(1)' \
      "$NPM_PACKAGE" "$NPM_NODE_GYP_DIR/package.json" && \
    test "$(node -p 'require("/usr/local/lib/node_modules/npm/node_modules/undici/package.json").version')" = "6.28.0" && \
    NPM_NODE_GYP_TARBALL=$(npm pack --silent --ignore-scripts --pack-destination /tmp "node-gyp@${NPM_NODE_GYP_VERSION}") && \
    NPM_NODE_GYP_UNDICI_TARBALL=$(npm pack --silent --ignore-scripts --pack-destination /tmp "undici@${NPM_NODE_GYP_UNDICI_VERSION}") && \
    node -e 'const fs=require("fs"); const crypto=require("crypto"); for(let i=1;i<process.argv.length;i+=2) { const actual=`sha512-${crypto.createHash("sha512").update(fs.readFileSync(process.argv[i])).digest("base64")}`; if(actual!==process.argv[i+1]) process.exit(1) }' \
      "/tmp/${NPM_NODE_GYP_TARBALL}" "$NPM_NODE_GYP_INTEGRITY" \
      "/tmp/${NPM_NODE_GYP_UNDICI_TARBALL}" "$NPM_NODE_GYP_UNDICI_INTEGRITY" && \
    rm -rf "$NPM_NODE_GYP_DIR" "$NPM_NODE_GYP_UNDICI_DIR" && \
    mkdir "$NPM_NODE_GYP_DIR" "$NPM_NODE_GYP_UNDICI_DIR" && \
    tar -xzf "/tmp/${NPM_NODE_GYP_TARBALL}" -C "$NPM_NODE_GYP_DIR" --strip-components=1 && \
    tar -xzf "/tmp/${NPM_NODE_GYP_UNDICI_TARBALL}" -C "$NPM_NODE_GYP_UNDICI_DIR" --strip-components=1 && \
    rm "/tmp/${NPM_NODE_GYP_TARBALL}" "/tmp/${NPM_NODE_GYP_UNDICI_TARBALL}" && \
    node -e 'const gyp=require(process.argv[1]); const undici=require(process.argv[2]); if(gyp.version!==process.argv[3] || gyp.dependencies.undici!=="^8.4.1" || undici.version!==process.argv[4]) process.exit(1)' \
      "$NPM_NODE_GYP_DIR/package.json" "$NPM_NODE_GYP_UNDICI_DIR/package.json" \
      "$NPM_NODE_GYP_VERSION" "$NPM_NODE_GYP_UNDICI_VERSION" && \
    (cd /usr/local/lib/node_modules/npm && npm ls node-gyp undici --all >/dev/null) && \
    node -e 'const {request}=require("/usr/local/lib/node_modules/npm/node_modules/undici"); if(typeof request!=="function") process.exit(1)' && \
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
    pm2@7.0.4 \
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

# Prisma 7.10.0 pins deepmerge-ts 7.1.5 and mysql2 3.15.3. Replace only those
# nested copies and materialize mysql2's required declaration peer from verified payloads.
RUN PRISMA_TYPES_NODE_INTEGRITY="sha512-6oYBAi5ikg4Pl+kGsoYtawUMBT2zZMCvPNF7pVLnHZfd1zf38DRiWn/gT01RYCdUqkv7Fhr+C9ot4/tb+2sVvA==" && \
    PRISMA_UNDICI_TYPES_INTEGRITY="sha512-iwDZqg0QAGrg9Rav5H4n0M64c3mkR59cJ6wQp+7C4nI0gsmExaedaYLNO44eT4AtBBwjbTiGPMlt2Md0T9H9JQ==" && \
    test "$(npm view "deepmerge-ts@${PRISMA_DEEPMERGE_VERSION}" dist.integrity)" = \
      "sha512-uqbvqLUMrc6p0MO+WBRtTxY55hmyh94WRwI5a++PZe54X+bfVh59FSN7uWCBCW1CCVjzjnrwzfI8zidE2obMMw==" && \
    test "$(npm view "mysql2@${PRISMA_MYSQL2_VERSION}" dist.integrity)" = \
      "sha512-X6Ujsr2QSkkLpkQGjxzpKRAPn9nu4axpR63ntBzquFVEvPOArgbUQ1sJjFKI7hnaYtiVZxa17Z7q18KSubW0IQ==" && \
    test "$(npm view "@types/node@${PRISMA_TYPES_NODE_VERSION}" dist.integrity)" = "$PRISMA_TYPES_NODE_INTEGRITY" && \
    test "$(npm view "undici-types@${PRISMA_UNDICI_TYPES_VERSION}" dist.integrity)" = "$PRISMA_UNDICI_TYPES_INTEGRITY" && \
    test "$(npm view "@prisma/config@${PRISMA_VERSION}" dependencies.deepmerge-ts)" = "7.1.5" && \
    test "$(npm view "prisma@${PRISMA_VERSION}" dependencies.mysql2)" = "3.15.3" && \
    PRISMA_DEEPMERGE_TARBALL=$(npm pack --silent --pack-destination /tmp \
      "deepmerge-ts@${PRISMA_DEEPMERGE_VERSION}") && \
    PRISMA_MYSQL2_TARBALL=$(npm pack --silent --pack-destination /tmp \
      "mysql2@${PRISMA_MYSQL2_VERSION}") && \
    PRISMA_TYPES_NODE_TARBALL=/tmp/prisma-types-node.tgz && \
    PRISMA_UNDICI_TYPES_TARBALL=/tmp/prisma-undici-types.tgz && \
    curl --disable --retry 8 --retry-all-errors --retry-max-time 300 --remove-on-error --connect-timeout 15 --max-time 300 -fsSL \
      -o "$PRISMA_TYPES_NODE_TARBALL" \
      "https://registry.npmjs.org/@types/node/-/node-${PRISMA_TYPES_NODE_VERSION}.tgz" && \
    curl --disable --retry 8 --retry-all-errors --retry-max-time 300 --remove-on-error --connect-timeout 15 --max-time 300 -fsSL \
      -o "$PRISMA_UNDICI_TYPES_TARBALL" \
      "https://registry.npmjs.org/undici-types/-/undici-types-${PRISMA_UNDICI_TYPES_VERSION}.tgz" && \
    node -e 'const fs=require("fs"); const crypto=require("crypto"); const actual=`sha512-${crypto.createHash("sha512").update(fs.readFileSync(process.argv[1])).digest("base64")}`; if(actual!==process.argv[2]) process.exit(1)' \
      "$PRISMA_TYPES_NODE_TARBALL" "$PRISMA_TYPES_NODE_INTEGRITY" && \
    node -e 'const fs=require("fs"); const crypto=require("crypto"); const actual=`sha512-${crypto.createHash("sha512").update(fs.readFileSync(process.argv[1])).digest("base64")}`; if(actual!==process.argv[2]) process.exit(1)' \
      "$PRISMA_UNDICI_TYPES_TARBALL" "$PRISMA_UNDICI_TYPES_INTEGRITY" && \
    PRISMA_DEEPMERGE_DIR=/usr/local/lib/node_modules/prisma/node_modules/deepmerge-ts && \
    PRISMA_MYSQL2_DIR=/usr/local/lib/node_modules/prisma/node_modules/mysql2 && \
    PRISMA_TYPES_NODE_DIR=/usr/local/lib/node_modules/prisma/node_modules/@types/node && \
    PRISMA_UNDICI_TYPES_DIR=/usr/local/lib/node_modules/prisma/node_modules/undici-types && \
    PRISMA_PACKAGE=/usr/local/lib/node_modules/prisma/package.json && \
    PRISMA_CONFIG_PACKAGE=/usr/local/lib/node_modules/prisma/node_modules/@prisma/config/package.json && \
    test "$(node -p 'require(process.argv[1]).version' "$PRISMA_PACKAGE")" = "${PRISMA_VERSION}" && \
    test ! -e "$PRISMA_TYPES_NODE_DIR" && \
    test ! -e "$PRISMA_UNDICI_TYPES_DIR" && \
    rm -rf "$PRISMA_DEEPMERGE_DIR" && mkdir "$PRISMA_DEEPMERGE_DIR" && \
    tar -xzf "/tmp/${PRISMA_DEEPMERGE_TARBALL}" -C "$PRISMA_DEEPMERGE_DIR" --strip-components=1 && \
    rm -rf "$PRISMA_MYSQL2_DIR" && mkdir "$PRISMA_MYSQL2_DIR" && \
    tar -xzf "/tmp/${PRISMA_MYSQL2_TARBALL}" -C "$PRISMA_MYSQL2_DIR" --strip-components=1 && \
    node -e 'const pkg=require(process.argv[1]); if(pkg.version!==process.argv[2] || pkg.peerDependencies["@types/node"]!==">= 8" || pkg.peerDependenciesMeta?.["@types/node"]!==undefined) process.exit(1)' \
      "$PRISMA_MYSQL2_DIR/package.json" "${PRISMA_MYSQL2_VERSION}" && \
    mkdir -p "$PRISMA_TYPES_NODE_DIR" "$PRISMA_UNDICI_TYPES_DIR" && \
    tar -xzf "$PRISMA_TYPES_NODE_TARBALL" -C "$PRISMA_TYPES_NODE_DIR" --strip-components=1 && \
    tar -xzf "$PRISMA_UNDICI_TYPES_TARBALL" -C "$PRISMA_UNDICI_TYPES_DIR" --strip-components=1 && \
    npm install --prefix "$PRISMA_MYSQL2_DIR" --ignore-scripts --package-lock=false --omit=dev && \
    rm "/tmp/${PRISMA_DEEPMERGE_TARBALL}" "/tmp/${PRISMA_MYSQL2_TARBALL}" \
      "$PRISMA_TYPES_NODE_TARBALL" "$PRISMA_UNDICI_TYPES_TARBALL" && \
    node -e 'const fs=require("fs"); const file=process.argv[1]; const version=process.argv[2]; const pkg=JSON.parse(fs.readFileSync(file,"utf8")); if(pkg.dependencies["deepmerge-ts"]!=="7.1.5") process.exit(1); pkg.dependencies["deepmerge-ts"]=version; fs.writeFileSync(file,`${JSON.stringify(pkg,null,2)}\n`)' \
      "$PRISMA_CONFIG_PACKAGE" "${PRISMA_DEEPMERGE_VERSION}" && \
    node -e 'const fs=require("fs"); const file=process.argv[1]; const version=process.argv[2]; const pkg=JSON.parse(fs.readFileSync(file,"utf8")); if(pkg.dependencies.mysql2!=="3.15.3") process.exit(1); pkg.dependencies.mysql2=version; fs.writeFileSync(file,`${JSON.stringify(pkg,null,2)}\n`)' \
      "$PRISMA_PACKAGE" "${PRISMA_MYSQL2_VERSION}" && \
    test "$(node -p 'require("/usr/local/lib/node_modules/prisma/node_modules/deepmerge-ts/package.json").version')" = \
      "${PRISMA_DEEPMERGE_VERSION}" && \
    test "$(node -p 'require("/usr/local/lib/node_modules/prisma/node_modules/mysql2/package.json").version')" = \
      "${PRISMA_MYSQL2_VERSION}" && \
    node -e 'const pkg=require(process.argv[1]); if(pkg.version!==process.argv[2] || pkg.types!=="index.d.ts" || pkg.main!=="" || pkg.dependencies["undici-types"]!=="~6.21.0") process.exit(1)' \
      "$PRISMA_TYPES_NODE_DIR/package.json" "${PRISMA_TYPES_NODE_VERSION}" && \
    test "$(node -p 'require(process.argv[1]).version' "$PRISMA_UNDICI_TYPES_DIR/package.json")" = \
      "${PRISMA_UNDICI_TYPES_VERSION}" && \
    test -s "$PRISMA_TYPES_NODE_DIR/index.d.ts" && \
    test -s "$PRISMA_UNDICI_TYPES_DIR/fetch.d.ts" && \
    node -e 'const resolved=require.resolve("@types/node/package.json",{paths:[process.argv[1]]}); const pkg=require(resolved); if(pkg.version!==process.argv[2] || resolved!==process.argv[3]) process.exit(1)' \
      "$PRISMA_MYSQL2_DIR" "${PRISMA_TYPES_NODE_VERSION}" "$PRISMA_TYPES_NODE_DIR/package.json" && \
    node -e 'const resolved=require.resolve("undici-types/package.json",{paths:[process.argv[1]]}); const pkg=require(resolved); if(pkg.version!==process.argv[2] || resolved!==process.argv[3]) process.exit(1)' \
      "$PRISMA_TYPES_NODE_DIR" "${PRISMA_UNDICI_TYPES_VERSION}" "$PRISMA_UNDICI_TYPES_DIR/package.json" && \
    (cd /usr/local/lib/node_modules/prisma && npm ls deepmerge-ts mysql2 @types/node undici-types --all >/dev/null) && \
    node -e 'const mysql=require("/usr/local/lib/node_modules/prisma/node_modules/mysql2"); if(typeof mysql.createConnection!=="function") process.exit(1)' && \
    prisma --version >/dev/null && \
    rm -rf /root/.npm

# PM2 7.0.4 directly pins vulnerable js-yaml 4.3.1. Replace only that nested
# package and bind the owner's exact dependency declaration to the fixed v4 release.
RUN PM2_JS_YAML_INTEGRITY="sha512-SFNOvSJ+Dgf/9An904Yx+CgSlIPCkIpao4qo51lpee25TIRejdH3rhR4EZMGoNx3/TP3O+wzWuiTFl4sqbltzA==" && \
    test "$(npm view "js-yaml@${PM2_JS_YAML_VERSION}" dist.integrity)" = "$PM2_JS_YAML_INTEGRITY" && \
    test "$(npm view pm2@7.0.4 dependencies.js-yaml)" = "4.3.1" && \
    PM2_PACKAGE=/usr/local/lib/node_modules/pm2/package.json && \
    PM2_JS_YAML_DIR=/usr/local/lib/node_modules/pm2/node_modules/js-yaml && \
    test "$(node -p 'require(process.argv[1]).version' "$PM2_PACKAGE")" = "7.0.4" && \
    test "$(node -p 'require("/usr/local/lib/node_modules/pm2/node_modules/js-yaml/package.json").version')" = \
      "4.3.1" && \
    node -e 'const pkg=require(process.argv[1]); if(pkg.dependencies["js-yaml"]!=="4.3.1") process.exit(1)' \
      "$PM2_PACKAGE" && \
    PM2_JS_YAML_TARBALL=$(npm pack --silent --ignore-scripts --pack-destination /tmp \
      "js-yaml@${PM2_JS_YAML_VERSION}") && \
    node -e 'const fs=require("fs"); const crypto=require("crypto"); const actual=`sha512-${crypto.createHash("sha512").update(fs.readFileSync(process.argv[1])).digest("base64")}`; if(actual!==process.argv[2]) process.exit(1)' \
      "/tmp/${PM2_JS_YAML_TARBALL}" "$PM2_JS_YAML_INTEGRITY" && \
    rm -rf "$PM2_JS_YAML_DIR" && mkdir "$PM2_JS_YAML_DIR" && \
    tar -xzf "/tmp/${PM2_JS_YAML_TARBALL}" -C "$PM2_JS_YAML_DIR" --strip-components=1 && \
    rm "/tmp/${PM2_JS_YAML_TARBALL}" && \
    node -e 'const fs=require("fs"); const file=process.argv[1]; const version=process.argv[2]; const pkg=JSON.parse(fs.readFileSync(file,"utf8")); if(pkg.dependencies["js-yaml"]!=="4.3.1") process.exit(1); pkg.dependencies["js-yaml"]=version; fs.writeFileSync(file,`${JSON.stringify(pkg,null,2)}\n`)' \
      "$PM2_PACKAGE" "${PM2_JS_YAML_VERSION}" && \
    test "$(node -p 'require("/usr/local/lib/node_modules/pm2/node_modules/js-yaml/package.json").version')" = \
      "${PM2_JS_YAML_VERSION}" && \
    node -e 'const pkg=require(process.argv[1]); if(pkg.dependencies["js-yaml"]!==process.argv[2]) process.exit(1)' \
      "$PM2_PACKAGE" "${PM2_JS_YAML_VERSION}" && \
    (cd /usr/local/lib/node_modules/pm2 && npm ls js-yaml --all >/dev/null) && \
    node -e 'const yaml=require("/usr/local/lib/node_modules/pm2/node_modules/js-yaml"); const parsed=yaml.load("service:\n  enabled: true\n"); if(parsed.service.enabled!==true) process.exit(1)' && \
    PM2_APP=/tmp/holycode-build-pm2-app.js && \
    printf 'setInterval(() => {}, 60000);\n' > "$PM2_APP" && \
    PM2_HOME=/tmp/holycode-build-pm2 pm2 start "$PM2_APP" --name holycode-build-pm2 --no-autorestart >/dev/null && \
    PM2_HOME=/tmp/holycode-build-pm2 pm2 --version | grep -Fx "7.0.4" && \
    PM2_HOME=/tmp/holycode-build-pm2 pm2 stop holycode-build-pm2 >/dev/null && \
    PM2_HOME=/tmp/holycode-build-pm2 pm2 kill >/dev/null && \
    rm -rf /tmp/holycode-build-pm2 "$PM2_APP" && \
    rm -rf /root/.npm

# PM2's get-uri 6.0.5 declares basic-ftp ^5.0.2, which has no fixed v5.
# Bind only that owner to 6.2.1; the FTP consumer is exercised below.
COPY scripts/test_get_uri_ftp.mjs /tmp/test_get_uri_ftp.mjs
RUN PM2_BASIC_FTP_INTEGRITY="sha512-bK67isD+lKq46AU8vNtjvMaT2ZqAOAmNCbxUHlFBRD4k15NWxyEjmaKtZPlgce58So4BNTjITGQOVTjL9y0ECA==" && \
    test "$(npm view "basic-ftp@${PM2_BASIC_FTP_VERSION}" dist.integrity)" = "$PM2_BASIC_FTP_INTEGRITY" && \
    PM2_ROOT=/usr/local/lib/node_modules/pm2 && \
    PM2_GET_URI_PACKAGE="$PM2_ROOT/node_modules/get-uri/package.json" && \
    PM2_BASIC_FTP_DIR="$PM2_ROOT/node_modules/basic-ftp" && \
    node -e 'const getUri=require(process.argv[1]); const ftp=require(process.argv[2]); if(getUri.version!=="6.0.5" || getUri.dependencies["basic-ftp"]!=="^5.0.2" || ftp.version!=="5.3.1") process.exit(1)' \
      "$PM2_GET_URI_PACKAGE" "$PM2_BASIC_FTP_DIR/package.json" && \
    PM2_BASIC_FTP_TARBALL=$(npm pack --silent --ignore-scripts --pack-destination /tmp "basic-ftp@${PM2_BASIC_FTP_VERSION}") && \
    node -e 'const fs=require("fs"); const crypto=require("crypto"); const actual=`sha512-${crypto.createHash("sha512").update(fs.readFileSync(process.argv[1])).digest("base64")}`; if(actual!==process.argv[2]) process.exit(1)' \
      "/tmp/${PM2_BASIC_FTP_TARBALL}" "$PM2_BASIC_FTP_INTEGRITY" && \
    rm -rf "$PM2_BASIC_FTP_DIR" && mkdir "$PM2_BASIC_FTP_DIR" && \
    tar -xzf "/tmp/${PM2_BASIC_FTP_TARBALL}" -C "$PM2_BASIC_FTP_DIR" --strip-components=1 && \
    node -e 'const fs=require("fs"); const file=process.argv[1]; const pkg=JSON.parse(fs.readFileSync(file,"utf8")); if(pkg.dependencies["basic-ftp"]!=="^5.0.2") process.exit(1); pkg.dependencies["basic-ftp"]=process.argv[2]; fs.writeFileSync(file,`${JSON.stringify(pkg,null,2)}\n`)' \
      "$PM2_GET_URI_PACKAGE" "$PM2_BASIC_FTP_VERSION" && \
    node -e 'const getUri=require(process.argv[1]); const ftp=require(process.argv[2]); if(getUri.dependencies["basic-ftp"]!==process.argv[3] || ftp.version!==process.argv[3]) process.exit(1)' \
      "$PM2_GET_URI_PACKAGE" "$PM2_BASIC_FTP_DIR/package.json" "$PM2_BASIC_FTP_VERSION" && \
    (cd "$PM2_ROOT" && npm ls get-uri basic-ftp --all >/dev/null) && \
    node /tmp/test_get_uri_ftp.mjs all && \
    rm "/tmp/${PM2_BASIC_FTP_TARBALL}" /tmp/test_get_uri_ftp.mjs && \
    rm -rf /root/.npm

# Wrangler 4.147.0 owns Miniflare 5.20261001.0-alpha and workerd 1.20261001.1;
# Miniflare owns the same workerd and the fixed Sharp release. Bind each owner.
RUN WRANGLER_SHARP_INTEGRITY="sha512-n++8XWcj+jCOr2IOl7h8LbKnGBDY4aPbmprMONBNFdn0ImXqpGVv5zliDs0V9HbmbCQLpbuo2ej9rAoOQTvMDA==" && \
    test "$(npm view "sharp@${WRANGLER_SHARP_VERSION}" dist.integrity)" = "$WRANGLER_SHARP_INTEGRITY" && \
    test "$(npm view "wrangler@${WRANGLER_VERSION}" dependencies.miniflare)" = "${WRANGLER_MINIFLARE_VERSION}" && \
    test "$(npm view "wrangler@${WRANGLER_VERSION}" dependencies.workerd)" = "1.20261001.1" && \
    test "$(npm view "miniflare@${WRANGLER_MINIFLARE_VERSION}" dependencies.sharp)" = "${WRANGLER_SHARP_VERSION}" && \
    test "$(npm view "miniflare@${WRANGLER_MINIFLARE_VERSION}" dependencies.workerd)" = "1.20261001.1" && \
    WRANGLER_PACKAGE=/usr/local/lib/node_modules/wrangler/package.json && \
    WRANGLER_NODE_MODULES=/usr/local/lib/node_modules/wrangler/node_modules && \
    WRANGLER_MINIFLARE_PACKAGE="$WRANGLER_NODE_MODULES/miniflare/package.json" && \
    WRANGLER_WORKERD_PACKAGE="$WRANGLER_NODE_MODULES/workerd/package.json" && \
    WRANGLER_SHARP_DIR="$WRANGLER_NODE_MODULES/sharp" && \
    test "$(node -p 'require(process.argv[1]).version' "$WRANGLER_PACKAGE")" = "${WRANGLER_VERSION}" && \
    node -e 'const pkg=require(process.argv[1]); if(pkg.dependencies.miniflare!==process.argv[2] || pkg.dependencies.workerd!=="1.20261001.1") process.exit(1)' \
      "$WRANGLER_PACKAGE" "${WRANGLER_MINIFLARE_VERSION}" && \
    node -e 'const pkg=require(process.argv[1]); if(pkg.version!==process.argv[2] || pkg.dependencies.sharp!==process.argv[3]) process.exit(1)' \
      "$WRANGLER_MINIFLARE_PACKAGE" "${WRANGLER_MINIFLARE_VERSION}" "${WRANGLER_SHARP_VERSION}" && \
    node -e 'const pkg=require(process.argv[1]); if(pkg.dependencies.workerd!=="1.20261001.1") process.exit(1)' \
      "$WRANGLER_MINIFLARE_PACKAGE" && \
    test "$(node -p 'require(process.argv[1]).version' "$WRANGLER_WORKERD_PACKAGE")" = \
      "1.20261001.1" && \
    test "$(node -p 'require(process.argv[1]).version' "$WRANGLER_SHARP_DIR/package.json")" = \
      "${WRANGLER_SHARP_VERSION}" && \
    case "${TARGETARCH}" in \
      amd64) WRANGLER_SHARP_ARCH=x64; \
        WRANGLER_SHARP_NATIVE_INTEGRITY="sha512-9qvvEAuk8k89TfWUoX2htWjbAMX8p+NxCppjpcg5k6xMsjhBQPTsoIh36h9Qde4WRuGpJeYnOjdosDn/cnv+OA=="; \
        WRANGLER_SHARP_LIBVIPS_INTEGRITY="sha512-4vKmvAst9nrowcqquKFAyZJUDolUaIp8uRiN0mWFguJ1IplC9/pitXtlnnlU4aa/eJw3J7i67V+pwUL+wZGdsA==";; \
      arm64) WRANGLER_SHARP_ARCH=arm64; \
        WRANGLER_SHARP_NATIVE_INTEGRITY="sha512-De4jpEnAU8Hd5oT0j1G3uL4ZvTuipVMn7YC6vPaJhy6/7EwEae0SVAoBrUMYQbkLGDm85taVWwuPc1a44LTzCQ=="; \
        WRANGLER_SHARP_LIBVIPS_INTEGRITY="sha512-0DaL0A6Xu6sQSQFwe4iVCrKWU2cCTItnRsYsCdxAMm9NF6twAA9BKnoqy4hqz4+azQ0JHuA26qiUKsf1XJ/v5A==";; \
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
    node -e 'const sharp=require(process.argv[1]); if(sharp.versions.sharp!==process.argv[2] || sharp.versions.heif!=="1.23.2") process.exit(1); sharp({create:{width:2,height:2,channels:4,background:{r:220,g:30,b:30,alpha:1}}}).avif().toBuffer().then(buffer=>sharp(buffer).raw().toBuffer({resolveWithObject:true})).then(({data,info})=>{if(info.width!==2 || info.height!==2 || info.channels!==4 || data.length!==16) process.exit(1)}).catch(error=>{console.error(error);process.exit(1)})' \
      "$WRANGLER_SHARP_DIR" "${WRANGLER_SHARP_VERSION}" && \
    ! command -v sharp && \
    rm -rf /root/.npm

RUN npm i -g --ignore-scripts \
    "paperclipai@${PAPERCLIP_VERSION}" && \
    rm -rf /root/.npm
# Paperclip's current Cursor SDK no longer installs Connect's Node transport.
# The remaining Undici is jsdom's 8.x dependency; guard the resolved owners.
RUN test "$(npm view "@cursor/sdk@${PAPERCLIP_CURSOR_SDK_VERSION}" dist.integrity)" = \
      "sha512-1Fpd644iTGNEoH5nEp5oYVlWgxSObL0VZfTZcCXhOB5MSJLc34vIvP6yx1udqSnpN+Rbpejvmxd9yoyjxhFVuw==" && \
    test "$(npm view "jsdom@${PAPERCLIP_JSDOM_VERSION}" dist.integrity)" = \
      "sha512-0FFE/jE1rppmVfUrJUgxqXjcwolZYIGtAgj1pTussMhNZxIxi7W/PvfWaMNroGi2B36X1IKHbexpZ9DhkoOPiQ==" && \
    test "$(npm view "undici@${PAPERCLIP_UNDICI_VERSION}" dist.integrity)" = \
      "sha512-u4UB2/IrKdU6lFxumHmmo1a3fCQO5tzQllRorfoRS63txhrB7xTpSn1PftwC4qEHkOaqP95fCWW4lJzwErwzhQ==" && \
    CONNECT_NODE_PACKAGE=/usr/local/lib/node_modules/paperclipai/node_modules/@connectrpc/connect-node/package.json && \
    test ! -e "$CONNECT_NODE_PACKAGE" && \
    test "$(find /usr/local/lib/node_modules/paperclipai -path '*/@connectrpc/connect-node/package.json' -type f | wc -l)" -eq 0 && \
    test "$(find /usr/local/lib/node_modules/paperclipai -path '*/undici/package.json' -type f | wc -l)" -eq 1 && \
    node -e 'const root="/usr/local/lib/node_modules/paperclipai/node_modules"; const adapter=require(`${root}/@paperclipai/adapter-cursor-cloud/package.json`); const sdk=require(`${root}/@cursor/sdk/package.json`); const server=require(`${root}/@paperclipai/server/package.json`); const jsdom=require(`${root}/jsdom/package.json`); const undici=require(`${root}/undici/package.json`); if(adapter.dependencies["@cursor/sdk"]!=="^1.0.28" || sdk.version!==process.argv[1] || sdk.dependencies["@connectrpc/connect-node"]!==undefined || server.dependencies.jsdom!=="^30.0.1" || jsdom.version!==process.argv[2] || jsdom.dependencies.undici!=="^8.11.2" || undici.version!==process.argv[3]) process.exit(1)' \
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

COPY scripts/rebuild_pip_seed_wheel.py /tmp/rebuild_pip_seed_wheel.py
COPY scripts/verify_pip_vendor_record.py /tmp/verify_pip_vendor_record.py
COPY scripts/test_pip_vendor_urllib3.py /tmp/test_pip_vendor_urllib3.py
RUN mkdir -p /usr/local/share/holycode/python-seed && \
    python3 -m pip download --no-deps --only-binary=:all: \
      --dest /usr/local/share/holycode/python-seed \
      --require-hashes -r /usr/local/share/holycode/python-seed-requirements.lock && \
    PIP_SEED=/usr/local/share/holycode/python-seed/pip-${PIP_VERSION}-py3-none-any.whl && \
    python3 /tmp/rebuild_pip_seed_wheel.py "$PIP_SEED" \
      /usr/local/lib/python3.13/dist-packages /tmp/pip-repaired-seed.whl && \
    mv /tmp/pip-repaired-seed.whl "$PIP_SEED" && \
    python3 -m venv /tmp/holycode-pip-seed-check && \
    /tmp/holycode-pip-seed-check/bin/python -m pip install --no-index --no-deps \
      --find-links /usr/local/share/holycode/python-seed \
      "pip==${PIP_VERSION}" "setuptools==${SETUPTOOLS_VERSION}" \
      "packaging==26.3" "wheel==0.48.0" && \
    /tmp/holycode-pip-seed-check/bin/python /tmp/verify_pip_vendor_record.py && \
    /tmp/holycode-pip-seed-check/bin/python /tmp/test_pip_vendor_urllib3.py && \
    /tmp/holycode-pip-seed-check/bin/python -c 'import pip._vendor.msgpack as m,pip._vendor.urllib3 as u; import pip._vendor.pkg_resources as p; assert m.__version__=="1.2.2" and u.__version__=="2.8.0" and p.get_distribution("pip").version=="26.2.1"' && \
    rm -rf /tmp/holycode-pip-seed-check \
      /tmp/rebuild_pip_seed_wheel.py /tmp/verify_pip_vendor_record.py /tmp/test_pip_vendor_urllib3.py

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
