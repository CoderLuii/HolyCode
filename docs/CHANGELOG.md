# Changelog

All notable changes to HolyCode will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.1.4] - 07/30/2026

### Added

- Add hash-locked Python requirements and a separately hash-locked offline pip, setuptools, Packaging, and wheel seed for new virtual environments
- Add exact, expiring security-exception records for Chromium fixes that Debian Trixie has not published yet

### Changed

- Refresh OpenCode to 1.18.9, Claude Code to 2.1.220, Paperclip to 2026.722.0, npm to 12.0.2, pnpm to 11.18.0, ESLint to 10.8.0, Wrangler to 4.115.0, Prisma to 7.9.1, and the protected Renovate validator to 44.2.3
- Refresh pip to 26.2, pandas to 3.0.5, tqdm to 4.70.0, FastAPI to 0.141.1, and Uvicorn to 0.52.0
- Upgrade Paperclip's reviewed nested Undici replacement to 6.28.0 and validate its installed dependency tree
- Rebuild GitHub CLI 2.96.0, fzf 0.74.1, and lazygit 0.63.1 from exact upstream commits with reviewed Go module security updates
- Install `opencode-claude-auth@2.1.5` from an integrity-verified payload included in the image instead of downloading it at container startup

### Removed

- Remove Netlify CLI and `serve` from the image
- Suspend HolyCode-managed oh-my-openagent installation while its current release tree retains unresolved security findings; stop without changes when the legacy flag is enabled, then disable the old active entry once the flag is removed while preserving settings, skills, and cached package data

### Fixed

- Test Paperclip migrations `0136` through `0183`, user membership, agent runtime state, plugin configuration, post-migration connections, restart persistence, and snapshot-only rollback from `v1.1.3`
- Replace npm's bundled `brace-expansion` and `tar` copies with 5.0.8 and 7.5.22 after verifying registry integrity
- Replace pip's vulnerable vendored msgpack and pkg_resources copies with hash-verified msgpack 1.2.1 and pkg_resources from setuptools 80.9.0
- Remove the root npm cache after reviewed lifecycle scripts run so package tarballs and stale dependency metadata do not remain in the final image
- Run protected release validation against the exact `v1.1.3` predecessor image and require the same candidate digest for publication

### Security

- Install Debian Chromium 150.0.7871.181 with its setuid sandbox enabled and record four unavailable `.186` fixes as exact 30-day exceptions
- Require zero unexcepted fixable critical and high findings from Docker Scout and Trivy on AMD64 and ARM64
- Pin `actions/setup-node` v7.0.0 and `docker/login-action` v4.6.0 by commit, bind protected validation to the exact `origin/main` commit, and validate exact scanner exceptions, plugin modes, release evidence, seccomp, workflows, Compose, and Renovate

## [1.1.3] - 07/21/2026

### Changed

- Refresh OpenCode to 1.18.4, Claude Code to 2.1.216, s6-overlay to 3.2.3.2, fzf to 0.74.1, pnpm to 11.15.1, Vite to 8.1.5, Prettier to 3.9.6, Wrangler to 4.112.0, Prisma to 7.9.0, Lighthouse to 13.4.1, and the default `oh-my-openagent` pin to 4.19.0
- Refresh pip to 26.1.2, Requests to 2.34.2, Pillow to 12.3.0, matplotlib to 3.11.1, tqdm to 4.69.0, FastAPI to 0.139.2, Packaging to 26.2, wheel to 0.47.0, and Rich to 15.0.0
- Keep Paperclip at 2026.707.0 while the 2026.720.0 migration chain receives separate persistence testing
- Run Chromium as `opencode` with its sandbox enabled through the shipped constrained seccomp profile
- Install the versioned PostgreSQL 17 client directly so vulnerability scanners do not attribute obsolete APT findings to its empty compatibility metapackage
- Rebuild GitHub CLI 2.96.0 from its exact upstream tag with digest-pinned Go 1.26.5 while the official package still embeds the vulnerable Go 1.26.4 standard library

### Removed

- Temporarily remove bundled Hermes while its release line requires vulnerable dependency pins; preserve existing `/home/opencode/.hermes` data and stop with a migration message when the legacy flag remains enabled
- Remove Vercel CLI, sharp-cli, concurrently, and LHCI because their current dependency trees contain fixable critical or high findings

### Fixed

- Replace Paperclip's vulnerable nested Undici 5.29.0 with Undici 6.27.0, align the installed Connect dependency declaration, and validate the Cursor adapter until Paperclip updates Connect upstream
- Install npm packages with lifecycle scripts disabled, then validate exact version, integrity, architecture, and script bodies before approved scripts run
- Define rollback as restoring untouched pre-upgrade volumes with image `1.1.2` instead of attempting an in-place database downgrade
- Restore the missing historical v1.0.3 changelog entry
- Promote the exact multi-architecture image digest built and scanned by protected validation instead of rebuilding mutable APT layers during publication

### Security

- Block protected releases on every fixable critical or high scanner finding
- Remove duplicate Debian pip/wheel package metadata after installing the fixed Python packages under `/usr/local`
- Remove the fixable `CVE-2026-39822` path from GitHub CLI and verify its source commit, embedded Go toolchain, and runtime version during the image build
- Update GitHub Actions pins and the Renovate validation pin, and add Chromium sandbox and nonblank Playwright screenshot gates
- Read Docker Scout's fixable-finding SARIF directly so scanner terminal-renderer failures cannot mask or manufacture a release-gate result

## [1.1.2] - 07/15/2026

### Added

- Add a deny-by-default npm 12 lifecycle policy that validates each installed package's exact version, script body, architecture, and allow/block decision

### Changed

- Migrate the image to the digest-pinned Node.js 24.18.0 Trixie base with Debian 13.6, Python 3.13.5, npm 12.0.1, and NumPy 2.5.1
- Refresh OpenCode to 1.18.2, Wrangler to 4.111.0, and lazygit to 0.63.1 while retaining Claude Code 2.1.210, Paperclip 2026.707.0, Hermes v2026.7.7.2, TypeScript 6.0.3, and Vercel 54.21.0
- Document that Wrangler's removed `legacy_env` mode is unsupported and that Netlify remains limited to remote build/deploy commands
- Move protected upgrade and rollback validation from `v1.1.0` to the published `v1.1.1` image and immutable manifest digest

### Fixed

- Run Paperclip's architecture-specific embedded PostgreSQL hydration script during the image build so its packaged library symlinks are ready before the service drops privileges
- Install Hermes' exact Packaging 26.0 requirement in `/usr/local` without trying to remove Trixie's dpkg-owned package
- Reclaim BuildKit's duplicate build cache before protected validation pulls the previous release image, preventing GitHub-hosted runners from exhausting disk space during upgrade and rollback checks

### Security

- Verify both architectures with Trivy 0.72.0 and Docker Scout 1.23.1: no fixable critical finding and no detected secret; record all residual high and unfixed critical findings in the release audit
- Confirm the Trixie image does not contain the fixable ImageMagick issue `CVE-2026-56367`; the newer unfixed `CVE-2026-56372` remains recorded in the audit

## [1.1.1] - 07/15/2026

### Changed

- Refresh OpenCode to 1.18.1, Claude Code to 2.1.210, s6-overlay to 3.2.3.1, pnpm to 11.13.0, tsx to 4.23.1, and the default `oh-my-openagent` pin to 4.18.1
- Refresh the immutable Node 24.18.0 Bookworm image digest and rebuild against current Bookworm repositories, including ImageMagick `deb12u12`
- Align Requests 2.33.0, Pillow 12.2.0, and Rich 14.3.3 with the exact dependency set required by Hermes v2026.7.7.2, then enforce `pip check` in the image build and smoke test
- Install Netlify CLI 26.2.0 without its platform-specific local functions binary and support remote build/deploy commands only
- Replace hard-coded upgrade assertions with release inputs and image metadata so validation compares the actual current and rollback images
- Validate Renovate configuration in pull requests and keep dependency updates behind maintainer review

### Removed

- Remove the bundled CLIProxyAPI sidecar and Compose profile while `v7.2.77` contains fixable high-severity Go dependencies; externally managed `CLIPROXYAPI_*` endpoints remain supported
- Remove the Netlify vulnerability exceptions because the affected binaries are no longer shipped

### Security

- Block releases on fixable critical findings and keep per-architecture Trivy, Docker Scout, SBOM, provenance, and secret checks in protected validation

### Fixed

- Register OpenCode, Xvfb, Paperclip, and Hermes through the `user-bundles.d` path required by s6-overlay 3.2.3.1

## [1.1.0] - 07/12/2026

### Changed

- Refresh the Docker runtime to Node.js 24.18.0 LTS with npm 11.16.0 after the full service matrix passed on Node 24
- Refresh OpenCode to 1.17.18, Paperclip to 2026.707.0, Hermes to v2026.7.7.2, CLIProxyAPI to v7.2.71, and the bundled release pins for eza, fzf, pnpm, Vite, ESLint, Prettier, Wrangler, Netlify CLI, tqdm, uvicorn, and Claude Code
- Retain Vercel 54.21.0 until authenticated scope/team behavior is proven, TypeScript 6.0.3 for stable toolchain APIs, NumPy 2.4.6 for Bookworm Python 3.11, and stable json-server 0.17.4 instead of its 1.0 beta
- Pin the default plugin packages to `opencode-claude-auth` 2.0.0 and `oh-my-openagent` 4.17.0, with `auto` syncing declared pins and `manual` preserving user versions
- Enforce one-digit release segments: `v1.0.9` rolls to `v1.1.0`, `v1.1.9` to `v1.2.0`, and `v1.9.9` to `v2.0.0`; published `v1.0.10` through `v1.0.13` remain immutable history
- Document Docker tags without the `v` prefix, digest/checksum/action-SHA hardening, per-platform SBOM and provenance attestations, and per-platform vulnerability scans without claiming byte-for-byte reproducibility, zero vulnerabilities, or universal freshness
- Clarify rollback guidance for copied bind mounts when a migration is not backward compatible, including the `1.0.13` Docker image (`v1.0.13` release) as the rollback target

### Fixed

- Run Hermes with the `opencode` user home and XDG paths instead of inheriting `/root`, preventing future dependency-level permission failures
- Keep OpenCode plugin installs on their exact declared versions across fresh, automatic, manual, and disabled startup modes
- Remove root npm download caches from build layers so package examples that resemble credentials are not shipped or scanned as runtime secrets
- Remove unsupported Hermes key-enforcement and reproducibility claims from the public docs

## [1.0.13] - 07/07/2026

### Changed

- Refresh the Docker runtime to Node.js 22.23.1 LTS while keeping npm 10.9.8
- Refresh pinned OpenCode, Paperclip, npm CLI, PyPI utility, GitHub-release, git-tag, and GitHub Actions versions in the Docker image and workflows
- Move Paperclip to its published Skills catalog package path and remove HolyCode's temporary catalog compatibility shim
- Update README, Docker Hub, Podman, translation, and third-party notice text for the current Paperclip catalog packaging

### Fixed

- Keep pull-request validation pointed at Paperclip's current Skills catalog manifest path

## [1.0.12] - 06/21/2026

### Changed

- Include Paperclip's published Skills catalog package in the Docker image until stable Paperclip carries the upstream package-layout fix
- Document the temporary Paperclip Skills catalog compatibility shim across the README, Docker Hub description, Podman guide, translations, and third-party notices

### Fixed

- Stop Paperclip's Skills page from failing on `GET /api/skills/catalog` by providing the catalog manifest at the path stable Paperclip expects
- Add pull-request validation that checks the Paperclip Skills catalog manifest and verifies a non-empty catalog can load from the built image

## [1.0.11] - 06/20/2026

### Changed

- Refresh Paperclip to 2026.618.0
- Document Paperclip's OpenCode home/config paths and the supported Docker update path across the README, Docker Hub description, Podman guide, examples, security notes, and translations

### Fixed

- Start Paperclip with the same `/home/opencode` HOME and XDG paths used by OpenCode so the OpenCode adapter no longer falls back to `/root/.config/opencode`
- Add pull-request validation that starts Paperclip and checks its runtime HOME/XDG environment

## [1.0.10] - 06/18/2026

### Changed

- Refresh the Docker runtime to Node.js 22.23.0 LTS with npm 10.9.8
- Refresh pinned npm, PyPI, GitHub-release, and git-tag tool versions in the Docker image
- Update GitHub Actions checkout/QEMU pins and add read-only permissions to read-only workflow jobs
- Migrate Renovate custom managers from `fileMatch` to `managerFilePatterns`
- Document the supported Docker update path, Hermes API key requirement, and the remaining third-party CLI audit caveat

### Fixed

- Remove the critical npm audit findings produced by the previous Dockerfile npm pin set
- Keep shell and s6 service files on LF endings so Docker images built from Windows checkouts start correctly
- Start Hermes in foreground mode under HolyCode's own s6 supervision
- Start Paperclip with a Docker-reachable bind preset and pre-create embedded Postgres compatibility symlinks

## [1.0.9] - 05/27/2026

### Added

- Add a dedicated Podman guide covering env-file setup, SELinux bind mounts, rootless permissions, updates, and minimal web UI usage

## [1.0.8] - 05/27/2026

### Fixed

- Allow Paperclip remote LAN/private hostnames to be configured with `PAPERCLIP_ALLOWED_HOSTNAMES`

## [1.0.7] - 05/27/2026

### Added

- Add optional CLIProxyAPI sidecar support in the full Docker Compose reference
- Add runtime OpenCode `cliproxyapi` provider wiring behind `CLIPROXYAPI_ENABLED`

### Changed

- Document CLIProxyAPI setup, environment variables, and isolated local-cache state paths in English docs

### Fixed

- Keep CLIProxyAPI configuration isolated from `ENABLE_CLAUDE_AUTH`, `opencode-claude-auth`, and Claude credential paths

## [1.0.6] - 05/27/2026

### Added

- Add Renovate-only dependency automation for GitHub Actions, Dockerfile pins, Docker ARGs, npm packages, and PyPI packages with automerge disabled

### Changed

- Pin Docker and runtime dependency versions for repeatable builds
- Refresh workflow action versions to current stable tags

### Fixed

- Preserve user-owned `oh-my-openagent-setup` skill folders while cleaning up HolyCode-managed copies when the plugin is disabled
- Document local `local-cache/` guidance for quick-start setups
- Repair translated README contributing links so they resolve to the source repo contribution guide

## [1.0.5] - 04/10/2026

### Added

- Add Hermes Agent as an optional bundled service with `ENABLE_HERMES`, persistent `~/.hermes` state, and an API surface on port `8642`
- Add Paperclip as an optional bundled service with `ENABLE_PAPERCLIP`, persistent `~/.paperclip` state, and a local dashboard on port `3100`
- Install Claude Code CLI in the image so the Claude Auth flow has the binary it expects
- Expand the shipped toolset with TypeScript, pnpm, Prisma, Lighthouse, database CLIs, media tools, and Python utility packages
- Add a pull-request validation workflow that builds the image and smoke-checks the OpenCode binary

### Changed

- Refresh the docs, translations, Docker Hub description, and landing page to reflect the new bundled services and the larger 50+ toolset
- Extend the default compose and env examples with Hermes and Paperclip toggles

### Fixed

- Resolve the `python-dotenv` and `dotenv-cli` binary collision so the image builds cleanly
- Switch Hermes to its foreground gateway runner and bootstrap Paperclip in a Docker-safe authenticated mode so both bundled services start correctly under s6-overlay
- Remove shell-expanded Python config edits from `entrypoint.sh` by passing data into Python safely
- Repair broken asset and LICENSE paths in the affected translated READMEs
- Remove stale Slim-variant references from the package request issue template

## [1.0.4] - 04/04/2026

### Added

- Ship a built-in `/oh-my-openagent-setup` skill for first-time setup and reruns after provider changes (only visible when `ENABLE_OH_MY_OPENAGENT=true`)
- Copy HolyCode-managed OpenCode skills into `~/.config/opencode/skills` on boot without overwriting existing user skill folders
- Ensure enabled plugin packages are installed on boot if they are missing from the OpenCode cache
- Add `HOLYCODE_PLUGIN_UPDATE` environment variable with two modes: `manual` (install if missing only) and `auto` (install if missing and update on boot)

### Changed

- Document `/oh-my-openagent-setup` as the supported path for writing `oh-my-openagent.jsonc`
- Document the default picker policy so only Sisyphus, Hephaestus, Prometheus, and Atlas are visible by default
- Clarify that `OPENCODE_DISABLE_AUTOUPDATE` only affects OpenCode itself, not plugins
- Clarify that `/oh-my-openagent-setup` skill only appears when the plugin is enabled

### Fixed

- Add an explicit rerun + doctor + model-capability refresh path for stale visible default-model behavior after provider changes

## [1.0.3] - 04/04/2026

### Added

- Ship a built-in `/oh-my-openagent-setup` skill for first-time setup and reruns after provider changes
- Copy HolyCode-managed OpenCode skills into `~/.config/opencode/skills` on boot without overwriting existing user skill folders
- Ensure enabled plugin packages are installed on boot if they are missing from the OpenCode cache

### Changed

- Document `/oh-my-openagent-setup` as the supported path for writing `oh-my-openagent.jsonc`
- Document the default picker policy so only Sisyphus, Hephaestus, Prometheus, and Atlas are visible by default

### Fixed

- Add an explicit rerun + doctor + model-capability refresh path for stale visible default-model behavior after provider changes

## [1.0.2] - 04/03/2026

### Changed

- Clarify that `/home/opencode` is the fixed container path while the host data path depends on the bind mount the user chooses
- Clarify that main data can live on remote storage while the cache path should remain local
- Clarify that `ENABLE_OH_MY_OPENAGENT=true` enables the plugin through `opencode.json` without promising a separate plugin-specific config file on the host

## [1.0.1] - 04/02/2026

### Fixed

- Detect CIFS/SMB network mounts and warn about SQLite WAL incompatibility
- Add `nobrl,mfsymlinks` mount option documentation for README Troubleshooting section

### Changed

- Expand SQLite WAL note with network storage guidance
- Add startup check in entrypoint.sh for CIFS/SMB detection
- Replace the `holycode-cache` named volume guidance with an explicit local-path cache bind mount for CIFS/SMB setups

## [1.0.0] - 03/30/2026

### Added
- OpenCode AI coding agent (v1.3.6) with built-in web UI on port 4096
- s6-overlay v3 for process supervision with auto-restart and clean shutdown
- Headless browser: Chromium + Xvfb + Playwright for browser automation
- Single bind mount persistence (all state under ./data/opencode)
- UID/GID remapping via PUID/PGID environment variables
- First-boot bootstrap with default config and git identity setup
- Claude Auth plugin toggle (ENABLE_CLAUDE_AUTH) for Claude subscription users
- oh-my-openagent plugin toggle (ENABLE_OH_MY_OPENAGENT) for multi-agent orchestration
- Web UI basic auth support (OPENCODE_SERVER_PASSWORD)
- 30+ dev tools: git, ripgrep, fd, fzf, bat, eza, lazygit, delta, gh CLI, htop, tmux, and more
- Language runtimes: Node.js 22, Python 3
- 10+ AI provider support: Anthropic, OpenAI, Gemini, Groq, AWS Bedrock, Azure OpenAI, Vertex AI, GitHub Models, Ollama
- CI/CD pipeline for Docker Hub + GHCR (amd64 + arm64)
- Docker Compose quick-start and full reference configurations
- Comprehensive README with quick start, troubleshooting, and architecture docs
- Landing page at holycode.coderluii.dev
