# ==============================================================================
# HolyCode - Pre-configured Docker Environment for OpenCode
# https://github.com/coderluii/holycode
# ==============================================================================

# renovate: datasource=github-releases depName=cli/cli
ARG GITHUB_CLI_VERSION=2.96.0
ARG GITHUB_CLI_REF=b300f2ec7ec9dc9addc39b2ad88c54097ded7ca0
# renovate: datasource=github-releases depName=junegunn/fzf
ARG FZF_VERSION=0.74.1
ARG FZF_REF=eae8d9d27eaeffc777699c01bf8f8b8c071908c1
# renovate: datasource=github-releases depName=jesseduffield/lazygit
ARG LAZYGIT_VERSION=0.63.1
ARG LAZYGIT_REF=aafe61082e7ed383d318fd40e48f85645e6afc7b

# Rebuild exact release sources with reviewed dependency fixes.
FROM --platform=$BUILDPLATFORM golang:1.26.5-trixie@sha256:4ee9ffa999b4583ce281939cdff828763083610292f252279a0cee77473bd9a7 AS github-cli-builder
ARG GITHUB_CLI_VERSION
ARG GITHUB_CLI_REF
ARG TARGETARCH
COPY patches/github-cli-modules.patch /tmp/github-cli-modules.patch
RUN git clone --branch "v${GITHUB_CLI_VERSION}" --depth 1 \
      https://github.com/cli/cli.git /src && \
    cd /src && \
    test "$(git rev-parse HEAD)" = "${GITHUB_CLI_REF}" && \
    test "$(git describe --tags --exact-match HEAD)" = "v${GITHUB_CLI_VERSION}" && \
    git apply --check /tmp/github-cli-modules.patch && \
    git apply /tmp/github-cli-modules.patch && \
    test "$(go list -m -f '{{.Version}}' google.golang.org/grpc)" = "v1.82.1" && \
    test "$(go list -m -f '{{.Version}}' golang.org/x/text)" = "v0.39.0" && \
    test "$(go list -m -f '{{.Version}}' github.com/klauspost/compress)" = "v1.18.7" && \
    go mod verify && \
    mkdir -p /tmp/gh-test && \
    chown -R nobody:nogroup /src /tmp/gh-test && \
    su -s /bin/sh nobody -c \
      'HOME=/tmp/gh-test GOCACHE=/tmp/gh-test/go-cache GOPATH=/tmp/gh-test/go go test ./...' && \
    git config --global --add safe.directory /src && \
    GH_GOARCH=$(case "$TARGETARCH" in arm64) echo "arm64";; *) echo "amd64";; esac) && \
    SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)" \
      GH_VERSION="${GITHUB_CLI_VERSION}" go run ./script/build.go bin/gh \
      GOOS=linux GOARCH="${GH_GOARCH}" CGO_ENABLED=0 && \
    install -D -m 0755 bin/gh /out/gh && \
    go version -m /out/gh | grep -F "go1.26.5" && \
    go version -m /out/gh | grep -E 'github.com/klauspost/compress[[:space:]]+v1\.18\.7' && \
    go version -m /out/gh | grep -E 'golang.org/x/text[[:space:]]+v0\.39\.0'

FROM --platform=$BUILDPLATFORM golang:1.26.5-trixie@sha256:4ee9ffa999b4583ce281939cdff828763083610292f252279a0cee77473bd9a7 AS fzf-builder
ARG FZF_VERSION
ARG FZF_REF
ARG TARGETARCH
COPY patches/fzf-x-sys-0.44.0.patch /tmp/fzf-x-sys-0.44.0.patch
RUN git clone --branch "v${FZF_VERSION}" --depth 1 \
      https://github.com/junegunn/fzf.git /src && \
    cd /src && \
    test "$(git rev-parse HEAD)" = "${FZF_REF}" && \
    test "$(git describe --tags --exact-match HEAD)" = "v${FZF_VERSION}" && \
    git apply --check /tmp/fzf-x-sys-0.44.0.patch && \
    git apply /tmp/fzf-x-sys-0.44.0.patch && \
    test "$(go list -m -f '{{.Version}}' golang.org/x/sys)" = "v0.44.0" && \
    go mod verify && \
    SHELL=/bin/sh go test \
      github.com/junegunn/fzf/src \
      github.com/junegunn/fzf/src/algo \
      github.com/junegunn/fzf/src/tui \
      github.com/junegunn/fzf/src/util && \
    mkdir -p /out && \
    FZF_GOARCH=$(case "$TARGETARCH" in arm64) echo "arm64";; *) echo "amd64";; esac) && \
    GOOS=linux GOARCH="${FZF_GOARCH}" CGO_ENABLED=0 go build -a -trimpath \
      -ldflags "-s -w -X main.version=${FZF_VERSION} -X main.revision=$(git rev-parse --short=8 HEAD)" \
      -o /out/fzf && \
    go version -m /out/fzf | grep -E 'golang.org/x/sys[[:space:]]+v0\.44\.0'

FROM --platform=$BUILDPLATFORM golang:1.26.5-trixie@sha256:4ee9ffa999b4583ce281939cdff828763083610292f252279a0cee77473bd9a7 AS lazygit-builder
ARG LAZYGIT_VERSION
ARG LAZYGIT_REF
ARG TARGETARCH
COPY patches/lazygit-x-text-0.39.0.patch /tmp/lazygit-x-text-0.39.0.patch
RUN git clone --branch "v${LAZYGIT_VERSION}" --depth 1 \
      https://github.com/jesseduffield/lazygit.git /src && \
    cd /src && \
    test "$(git rev-parse HEAD)" = "${LAZYGIT_REF}" && \
    test "$(git describe --tags --exact-match HEAD)" = "v${LAZYGIT_VERSION}" && \
    git apply --check /tmp/lazygit-x-text-0.39.0.patch && \
    git apply /tmp/lazygit-x-text-0.39.0.patch && \
    export GOFLAGS=-mod=mod && \
    test "$(go list -m -f '{{.Version}}' golang.org/x/text)" = "v0.39.0" && \
    go mod verify && \
    LAZYGIT_MODULE_FILES_SHA256="$(sha256sum go.mod go.sum)" && \
    go mod vendor && \
    test "$(sha256sum go.mod go.sum)" = "${LAZYGIT_MODULE_FILES_SHA256}" && \
    export GOFLAGS=-mod=vendor && \
    go test ./... && \
    mkdir -p /out && \
    LAZYGIT_GOARCH=$(case "$TARGETARCH" in arm64) echo "arm64";; *) echo "amd64";; esac) && \
    BUILD_DATE="$(git show -s --format=%cI HEAD)" && \
    GOOS=linux GOARCH="${LAZYGIT_GOARCH}" CGO_ENABLED=0 go build -trimpath \
      -ldflags "-s -w -X main.version=${LAZYGIT_VERSION} -X main.commit=${LAZYGIT_REF} -X main.date=${BUILD_DATE} -X main.buildSource=binaryRelease" \
      -o /out/lazygit && \
    go version -m /out/lazygit | grep -E 'golang.org/x/text[[:space:]]+v0\.39\.0'

FROM node:24.18.0-trixie-slim@sha256:ae91dcc111a68c9d2d81ff2a17bda61be126426176fde6fe7d08ab13b7f50573

# ---------- Build args ----------
ARG GITHUB_CLI_VERSION
ARG FZF_VERSION
ARG LAZYGIT_VERSION
# renovate: datasource=github-releases depName=just-containers/s6-overlay
ARG S6_OVERLAY_VERSION=3.2.3.2
# renovate: datasource=github-releases depName=dandavison/delta
ARG DELTA_VERSION=0.19.2
# renovate: datasource=github-releases depName=eza-community/eza
ARG EZA_VERSION=0.23.5
# renovate: datasource=npm depName=opencode-ai
ARG OPENCODE_VERSION=1.18.9
# renovate: datasource=npm depName=@anthropic-ai/claude-code
ARG CLAUDE_CODE_VERSION=2.1.220
# renovate: datasource=npm depName=paperclipai
ARG PAPERCLIP_VERSION=2026.722.0
# renovate: datasource=npm depName=undici
ARG PAPERCLIP_UNDICI_VERSION=6.28.0
# renovate: datasource=npm depName=opencode-claude-auth
ARG CLAUDE_AUTH_PLUGIN_VERSION=2.1.5
# renovate: datasource=npm depName=typescript
ARG TYPESCRIPT_VERSION=6.0.3
# renovate: datasource=npm depName=npm
ARG NPM_VERSION=12.0.2
# renovate: datasource=npm depName=brace-expansion
ARG NPM_BRACE_EXPANSION_VERSION=5.0.8
# renovate: datasource=npm depName=tar
ARG NPM_TAR_VERSION=7.5.22
# renovate: datasource=npm depName=tsx
ARG TSX_VERSION=4.23.1
# renovate: datasource=npm depName=pnpm
ARG PNPM_VERSION=11.18.0
# renovate: datasource=npm depName=vite
ARG VITE_VERSION=8.1.5
# renovate: datasource=npm depName=prettier
ARG PRETTIER_VERSION=3.9.6
# renovate: datasource=npm depName=prisma
ARG PRISMA_VERSION=7.9.1
# renovate: datasource=npm depName=lighthouse
ARG LIGHTHOUSE_VERSION=13.4.1
# renovate: datasource=npm depName=wrangler
ARG WRANGLER_VERSION=4.115.0
# renovate: datasource=npm depName=eslint
ARG ESLINT_VERSION=10.8.0
# renovate: datasource=pypi depName=numpy
ARG NUMPY_VERSION=2.5.1
# renovate: datasource=pypi depName=pip
ARG PIP_VERSION=26.2
# renovate: datasource=pypi depName=msgpack
ARG PIP_VENDOR_MSGPACK_VERSION=1.2.1
ARG PIP_VENDOR_MSGPACK_SHA256=04c721c2c7448767e9e3f2520a475663d8ee0f09c31890f6d2bd70fd636a9647
# pkg_resources was removed in setuptools 81; keep its last fixed source.
ARG PIP_VENDOR_PKG_RESOURCES_VERSION=80.9.0
ARG PIP_VENDOR_PKG_RESOURCES_SHA256=f36b47402ecde768dbfafc46e8e4207b4360c654f1f3bb84475f0a28628fb19c
# renovate: datasource=pypi depName=setuptools
ARG SETUPTOOLS_VERSION=83.0.0
ARG RELEASE_APT_REFRESH=2026-07-30
ARG TARGETARCH

LABEL org.opencontainers.image.source=https://github.com/CoderLuii/HolyCode \
    io.holycode.version.github-cli=${GITHUB_CLI_VERSION} \
    io.holycode.version.opencode=${OPENCODE_VERSION} \
    io.holycode.version.claude-code=${CLAUDE_CODE_VERSION} \
    io.holycode.version.paperclip=${PAPERCLIP_VERSION} \
    io.holycode.version.claude-auth-plugin=${CLAUDE_AUTH_PLUGIN_VERSION} \
    io.holycode.version.npm=${NPM_VERSION} \
    io.holycode.version.npm-brace-expansion=${NPM_BRACE_EXPANSION_VERSION} \
    io.holycode.version.npm-tar=${NPM_TAR_VERSION} \
    io.holycode.version.pip-vendor-msgpack=${PIP_VENDOR_MSGPACK_VERSION} \
    io.holycode.version.pip-vendor-pkg-resources=${PIP_VENDOR_PKG_RESOURCES_VERSION} \
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
COPY --from=fzf-builder /out/fzf /usr/local/bin/fzf

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
COPY --from=lazygit-builder /out/lazygit /usr/local/bin/lazygit
RUN lazygit --version | grep -F "version=${LAZYGIT_VERSION}"

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
    && dpkg-query -W -f='${Version}\n' chromium | grep -E '^150\.0\.7871\.(18[1-9]|19[0-9]|[2-9][0-9]{2,})-' \
    && test "$(dpkg-query -W -f='${Version}' chromium)" = "$(dpkg-query -W -f='${Version}' chromium-sandbox)" \
    && rm -rf /var/lib/apt/lists/*

# ---------- Python packages ----------
COPY config/python-requirements.lock /usr/local/share/holycode/python-requirements.lock
COPY config/python-seed-requirements.lock /usr/local/share/holycode/python-seed-requirements.lock
COPY patches/pip-vendored-pkg-resources-80.9.0.patch /tmp/pip-vendored-pkg-resources.patch
RUN python3 -m pip install --no-cache-dir --break-system-packages --ignore-installed \
      --require-hashes -r /usr/local/share/holycode/python-requirements.lock

# Replace Debian's vulnerable wheel metadata after installing fixed copies in
# /usr/local. pip remains available from the exact PyPI package.
RUN python3 -m pip install --no-cache-dir --break-system-packages --ignore-installed \
      --require-hashes -r /usr/local/share/holycode/python-seed-requirements.lock && \
    curl -fsSL -o /tmp/msgpack.tar.gz \
      "https://files.pythonhosted.org/packages/31/f9/c0a1c127f9049db9155afc316952ea571720dd01833ff5e4d7e8e6352dbb/msgpack-${PIP_VENDOR_MSGPACK_VERSION}.tar.gz" && \
    echo "${PIP_VENDOR_MSGPACK_SHA256}  /tmp/msgpack.tar.gz" | sha256sum -c - && \
    curl -fsSL -o /tmp/setuptools.tar.gz \
      "https://files.pythonhosted.org/packages/18/5d/3bf57dcd21979b887f014ea83c24ae194cfcd12b9e0fda66b957c69d1fca/setuptools-${PIP_VENDOR_PKG_RESOURCES_VERSION}.tar.gz" && \
    echo "${PIP_VENDOR_PKG_RESOURCES_SHA256}  /tmp/setuptools.tar.gz" | sha256sum -c - && \
    mkdir -p /tmp/msgpack /tmp/setuptools && \
    tar -xzf /tmp/msgpack.tar.gz -C /tmp/msgpack --strip-components=1 && \
    tar -xzf /tmp/setuptools.tar.gz -C /tmp/setuptools --strip-components=1 && \
    (cd /tmp/setuptools && patch -p1 < /tmp/pip-vendored-pkg-resources.patch) && \
    PIP_VENDOR_DIR="$(python3 -c 'import pathlib,pip._vendor; print(pathlib.Path(pip._vendor.__file__).parent)')" && \
    rm -rf "$PIP_VENDOR_DIR/msgpack" "$PIP_VENDOR_DIR/pkg_resources" && \
    cp -a /tmp/msgpack/msgpack "$PIP_VENDOR_DIR/msgpack" && \
    cp -a /tmp/setuptools/pkg_resources "$PIP_VENDOR_DIR/pkg_resources" && \
    cp /tmp/msgpack/COPYING "$PIP_VENDOR_DIR/msgpack/COPYING" && \
    cp /tmp/setuptools/LICENSE "$PIP_VENDOR_DIR/pkg_resources/LICENSE" && \
    rm -rf "$PIP_VENDOR_DIR/pkg_resources/tests" "$PIP_VENDOR_DIR/pkg_resources/api_tests.txt" && \
    sed -i \
      "s/^msgpack==.*/msgpack==${PIP_VENDOR_MSGPACK_VERSION}/; s/^setuptools==.*/setuptools==${PIP_VENDOR_PKG_RESOURCES_VERSION}/" \
      "$PIP_VENDOR_DIR/vendor.txt" && \
    python3 -c 'import json,pathlib,sys; path=pathlib.Path(sys.argv[1]); data=json.loads(path.read_text()); versions={"msgpack":sys.argv[2],"setuptools":sys.argv[3]}; [(component.update(version=versions[component["name"]],purl="pkg:pypi/{0}@{1}".format(component["name"],versions[component["name"]])) if component.get("name") in versions else None) for component in data.get("components",[])]; path.write_text(json.dumps(data,indent=2)+"\n")' \
      "$PIP_VENDOR_DIR/bom.cdx.json" "$PIP_VENDOR_MSGPACK_VERSION" "$PIP_VENDOR_PKG_RESOURCES_VERSION" && \
    rm -rf \
      /tmp/msgpack /tmp/setuptools /tmp/msgpack.tar.gz /tmp/setuptools.tar.gz \
      /tmp/pip-vendored-pkg-resources.patch && \
    apt-get purge -y python3-pip python3-wheel && \
    rm -rf /var/lib/apt/lists/* && \
    python3 -m pip --version | grep -F "pip ${PIP_VERSION}" && \
    python3 -c 'import pip._vendor.msgpack as msgpack; assert msgpack.__version__ == "1.2.1"; import pip._vendor.pkg_resources' && \
    _PIP_USE_IMPORTLIB_METADATA=0 python3 -m pip list --format=json >/dev/null && \
    python3 -c 'import setuptools; assert setuptools.__version__ == "83.0.0"' && \
    python3 -m pip check

RUN rm -f /usr/local/bin/dotenv

RUN npm install -g --ignore-scripts "npm@${NPM_VERSION}" && \
    test "$(npm --version)" = "${NPM_VERSION}" && \
    rm -rf /root/.npm
RUN test "$(npm view "brace-expansion@${NPM_BRACE_EXPANSION_VERSION}" dist.integrity)" = \
      "sha512-JZyDyq3D4AUifKTPOB7DELf6XsB3WdPuNxCtob1vFXPsSXhdAiHBWJ/tJ8HAc9aH84BK+5JFZLNkJKx3G9kzQg==" && \
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
    "eslint@${ESLINT_VERSION}" "prettier@${PRETTIER_VERSION}" \
    nodemon@3.1.14 \
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

RUN npm i -g --ignore-scripts \
    "paperclipai@${PAPERCLIP_VERSION}" && \
    rm -rf /root/.npm
# Paperclip's Cursor adapter currently resolves Undici 5 through Connect 1.x.
# Keep Paperclip stable while replacing that HTTP client with the first fixed
# 6.x release; remove this reviewed compatibility patch when Paperclip updates Connect.
RUN test "$(npm view "undici@${PAPERCLIP_UNDICI_VERSION}" dist.integrity)" = \
      "sha512-LIY910g9TI13YS95lrMFrs8Rm/u/irgHeTWoKCoteeJ04CUJ92eEfj0rVn+7VKMPBpUPiUoBKfhNyLI23EE/KA==" && \
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
    node --input-type=module -e 'const {testEnvironment}=await import("file:///usr/local/lib/node_modules/paperclipai/node_modules/@paperclipai/adapter-cursor-cloud/dist/server/index.js"); const result=await testEnvironment({adapterType:"cursor_cloud",config:{}}); if(result.status!=="fail" || !result.checks.some((check)=>check.code==="cursor_cloud_api_key_missing")) process.exit(1)' && \
    rm -rf /root/.npm
# Package the supported Claude Auth plugin for network-free startup.
RUN test "$(npm view "opencode-claude-auth@${CLAUDE_AUTH_PLUGIN_VERSION}" dist.integrity)" = \
      "sha512-rRZ3aZJEbgHsXzox1vkXY3sIrE3Z6c5ya/hEJJb2/XavuPufvTLI9dN2VHfvhFTl6eZPbs10hlSirfGnyLr46Q==" && \
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
    esbuild --version | grep -Fx "0.28.1" && \
    prisma --version >/dev/null && \
    wrangler --version | grep -F "${WRANGLER_VERSION}" && \
    ! command -v vercel && ! command -v sharp && ! command -v concurrently && \
    ! command -v lhci && ! command -v netlify && ! command -v serve && \
    WORKERD_BIN=$(find /usr/local/lib/node_modules/wrangler -path '*/workerd/bin/workerd' -type f -print -quit) && \
    test -n "${WORKERD_BIN}" && "${WORKERD_BIN}" --version >/dev/null && \
    node -e 'const ssh2=require("/usr/local/lib/node_modules/paperclipai/node_modules/ssh2"); if(typeof ssh2.Client!=="function") process.exit(1)' && \
    rm -rf /root/.npm

RUN mkdir -p /usr/local/share/holycode/python-seed && \
    python3 -m pip download --no-deps --only-binary=:all: \
      --dest /usr/local/share/holycode/python-seed \
      --require-hashes -r /usr/local/share/holycode/python-seed-requirements.lock

RUN mkdir -p /usr/local/share/holycode && \
    dpkg-query -W -f='${binary:Package}\t${Version}\n' | sort > /usr/local/share/holycode/dpkg-inventory.txt

# ---------- Copy config files ----------
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY scripts/bootstrap.sh /usr/local/bin/bootstrap.sh
COPY config/opencode.json /usr/local/share/holycode/opencode.json
COPY config/security-exceptions-v1.1.4.json /usr/local/share/holycode/security-exceptions-v1.1.4.json
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
