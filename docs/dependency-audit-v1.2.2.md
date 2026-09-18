# HolyCode v1.2.2 Dependency Audit

Date: 09/18/2026

Git predecessor `v1.2.1` is the supported release baseline. Upgrade and rollback validation uses `coderluii/holycode:1.2.1@sha256:12382641397dd477fe4a57a7dcf74107b05062c5285f0f50cc8664056701a2b2`.

This audit records the selected v1.2.2 source graph. It is not a publication record. The notice-bound candidate still needs final native AMD64 and ARM64 builds, installed-notice equality, complete runtime/plugin and upgrade/rollback checks, per-platform SBOM and provenance, scanners, artifact checksums, and registry alias verification for the exact release digest.

## Selected updates

| Component | v1.2.1 | v1.2.2 | Decision and source |
| --- | --- | --- | --- |
| Node.js base | `24.21.0-trixie-slim@sha256:db3ae80f5d8df06e04dabdf7b44cbf008d32de168205fa0294444aabbc08c590` | `24.21.0-trixie-slim@sha256:d7b4e5c4ad20b327d7bb16fab6aecd60ac20aa50f8514eb75a2b059e89abe48e` | Same Node 24 LTS release, refreshed official OCI index; rebuild and scan required. [Node releases](https://nodejs.org/dist/index.json) |
| GitHub CLI | 2.100.0 | 2.101.0 | Build exact signed upstream commit `0cf1092493af067646fc5f3db9421c6a6ec9c938`. [Release](https://github.com/cli/cli/releases/tag/v2.101.0) |
| OpenCode | 1.18.30 | 1.18.31 | Exact npm integrity and unchanged reviewed postinstall body. [Registry](https://registry.npmjs.org/opencode-ai/1.18.31) |
| Claude Code | 2.1.270 | 2.1.276 | Exact npm integrity and unchanged reviewed postinstall body. [Registry](https://registry.npmjs.org/@anthropic-ai%2fclaude-code/2.1.276) |
| OpenSpec (`@fission-ai/openspec`) | 1.13.0 | 1.13.1 | No install lifecycle script; telemetry stays disabled and project initialization stays explicit. [Registry](https://registry.npmjs.org/@fission-ai%2fopenspec/1.13.1) |
| pnpm | 12.4.1 | 12.4.2 | Lifecycle scripts remain blocked; offline execution remains an image check. [Registry](https://registry.npmjs.org/pnpm/12.4.2) |
| Prettier | 3.9.6 | 3.9.8 | Direct stable update with no package lifecycle script. [Registry](https://registry.npmjs.org/prettier/3.9.8) |
| Wrangler | 4.131.2 | 4.134.0 | Direct stable update with its exact owner-selected Miniflare/workerd graph. [Registry](https://registry.npmjs.org/wrangler/4.134.0) |
| Playwright | 1.62.0 | 1.63.0 | Direct Python update; AMD64 install/import passed and ARM64 wheel availability was verified. System-Chromium execution remains an image gate. [PyPI](https://pypi.org/project/playwright/1.63.0/) |
| pandas | 3.0.5 | 3.0.6 | Direct Python update; AMD64 import/round-trip passed and CPython 3.13 ARM64 wheel availability was verified. [PyPI](https://pypi.org/project/pandas/3.0.6/) |
| Renovate validator | 44.87.1 | 44.97.6 | CI-only exact version; strict config validation and extraction passed in a real Linux git repository. [Registry](https://registry.npmjs.org/renovate/44.97.6) |

The Node base tag kept the same release number but changed index digest. Go remains `1.27.1-trixie@sha256:9baa6b4187bbb98d240372a8a235ac0bb6b5ddd52bba1431dc2f7c0705862728`.

## Direct image tools

These are the direct versioned tools and runtimes selected by the Dockerfile. `Current` means the reviewed stable selection did not change in v1.2.2; it does not promise that a mutable registry tag will never move.

| Tool or runtime | Selected version | Outcome |
| --- | ---: | --- |
| Node.js / npm | 24.21.0 / 12.0.2 | Node digest refreshed; npm version current and unchanged |
| Python / pip / setuptools | 3.13 / 26.2.1 / 84.0.0 | Current direct runtime/tool pins |
| Go builder | 1.27.1 | Current, unchanged |
| GitHub CLI | 2.101.0 | Updated |
| OpenCode | 1.18.31 | Updated |
| Claude Code | 2.1.276 | Updated |
| Paperclip | 2026.831.1 | Compatibility hold; details below |
| OpenSpec | 1.13.1 | Updated |
| opencode-claude-auth | 2.2.0 | Current published plugin; reported refresh defect unresolved |
| TypeScript | 6.0.3 | Compatibility hold; details below |
| PM2 | 7.0.4 | Current, unchanged |
| tsx | 4.23.13 | Current, unchanged |
| pnpm | 12.4.2 | Updated |
| Vite | 8.3.0 | Current, unchanged |
| Prettier | 3.9.8 | Updated |
| Prisma | 7.10.0 | Stable hold; details below |
| Lighthouse | 13.4.1 | Current, unchanged |
| Wrangler / Miniflare / workerd | 4.134.0 / 5.20260917.0-alpha / 1.20260917.1 | Wrangler updated; owned graph retained exactly |
| ESLint | 10.10.0 | Current, unchanged |
| s6-overlay | 3.2.3.2 | Current, unchanged |
| delta / eza | 0.19.2 / 0.23.5 | Current, unchanged |
| fzf / lazygit | 0.74.4 / 0.65.1 | Current source builds from pinned upstream commits |
| json-server | 0.17.4 | Stable hold; details below |
| Chromium | Debian Trixie package | Distro-managed; exact final package version belongs to the release SBOM |

Hermes and HolyCode-managed oh-my-openagent installation remain suspended. CLIProxyAPI remains an externally managed endpoint, not a bundled sidecar. Netlify CLI, `serve`, Vercel, sharp-cli, concurrently, and LHCI remain outside the image.

## Direct Python application set

The complete direct application input is hash-locked. Only Playwright and pandas changed; every other direct pin was reviewed and retained.

| Area | Selected direct packages |
| --- | --- |
| Packaging | packaging 26.3, wheel 0.48.0, setuptools 84.0.0 |
| HTTP and documents | requests 2.34.2, httpx 0.28.1, beautifulsoup4 4.15.0, lxml 6.1.3, Pillow 12.3.0, openpyxl 3.1.5, python-docx 1.2.0 |
| Data and plotting | pandas 3.0.6, NumPy 2.5.3, Matplotlib 3.11.2, seaborn 0.13.2 |
| Browser | Playwright 1.63.0 |
| CLI and notifications | rich 15.0.0, Click 8.5.0, tqdm 4.70.1, apprise 1.13.1 |
| Templates and config | Jinja2 3.1.6, PyYAML 6.0.3, python-dotenv 1.2.3, Markdown 3.10.3 |
| Web runtime | FastAPI 0.141.1, Uvicorn 0.53.0 |

A clean resolve from deleted output updated compatible transitives contourpy 1.4.0, greenlet 3.5.6, idna 3.20, and urllib3 2.8.0. It retained `pydantic-core 2.46.5` because Pydantic owns that exact constraint and `pyee 13.0.1` because Playwright requires a version below 14.

The accepted locks were generated with Python 3.13.15, pip 26.2.1, pip-tools 7.6.1, and resolver-only Click 8.4.2. Product `click==8.5.0` remains unchanged. pip-tools 7.6.1 still writes a false `--no-index` header when its updater environment resolves Click 8.5.0. Upstream issue [#2472](https://github.com/jazzband/pip-tools/issues/2472) and fix PR [#2475](https://github.com/jazzband/pip-tools/pull/2475) remain open. Automatic pip-tools lock updates are therefore still blocked; no wrapper, manager disablement, product downgrade, or fabricated header was added.

## Owner-scoped graph and replacement inventory

These versions are not independent top-level tool claims. Each stays inside the named owner boundary and is checked against that owner's declared graph or HolyCode's reviewed raw replacement.

| Owner boundary | Selected component | Outcome and rationale |
| --- | --- | --- |
| GitHub CLI 2.101.0 | `klauspost/compress` 1.20.0, `x/text` 0.42.0, `x/mod` 0.41.0 | Updated to the release's upstream `go.mod`; the old local x/mod override was removed |
| fzf 0.74.4 | `x/sys` 0.44.0 | Existing reviewed source patch retained |
| npm 12.0.2 / minimatch | `brace-expansion` 5.0.12 | Updated raw npm payload inside the accepted owner range |
| npm 12.0.2 | `tar` 7.5.22 | Existing raw replacement retained |
| npm 12.0.2 / socks | `ip-address` 10.7.2 | Updated raw npm payload inside the accepted owner range |
| PM2 7.0.4 | `js-yaml` 4.3.2 | Existing v4-compatible raw replacement retained; 5.x remains a major-boundary hold |
| Paperclip 2026.831.1 | Undici 6.28.1 | Existing owner-compatible replacement retained; 8.x crosses two majors |
| Paperclip 2026.831.1 | embedded PostgreSQL 18.1.0-beta.16 native packages | Existing architecture-specific lifecycle entries retained |
| Prisma 7.10.0 | deepmerge-ts 8.0.2, mysql2 3.24.4 | Existing owner-scoped replacements retained |
| Prisma / mysql2 | `@types/node` 20.19.43, `undici-types` 6.21.0 | Existing type-only peer/declaration payloads retained |
| Wrangler 4.134.0 | Miniflare 5.20260917.0-alpha, workerd 1.20260917.1 | Exact versions declared by Wrangler; workerd is not an independent latest pin |
| Miniflare | Sharp 0.35.4 and libvips 1.3.3 | Existing owner graph retained and byte-checked in image validation |
| pip 26.2.1 | vendored msgpack 1.2.2 | Existing hash-verified vendor replacement retained |
| pip 26.2.1 | pkg_resources from setuptools 78.1.1 | Existing checksum-verified vendor replacement retained |

Prisma's existing type-only peer remains @types/node 20.19.43 with undici-types 6.21.0 beside it. Both are raw, owner-scoped declaration payloads; neither is a new top-level runtime tool.

The complete global npm diagnostic remains bounded to the two accepted owner findings: Lighthouse 13.4.1 owns @paulirish/trace_engine 0.0.65, whose literal latest declarations resolve to third-party-web 0.29.2 and legacy-javascript 0.0.1. Missing peers or any changed/additional finding fail the smoke. This is not a universal clean-tree claim.

Drizzle ORM 0.45.2 is already a Paperclip transitive in both v1.2.1 and the held v1.2.2 graph. HolyCode also has a direct smoke fixture for it. Drizzle is not a new top-level HolyCode tool or a v1.2.2 dependency change.

Paperclip's packaged catalog is validated as package data. The held package contains 16 local entries with 27 verified local files plus one optional pinned remote descriptor with 79 metadata records. HolyCode does not materialize the remote records in user-managed configuration and does not write a user skill directory during image smoke.

## Compatibility holds and unresolved items

| Component | Retained | Evaluated alternative | Why it remains held | Unlock condition |
| --- | ---: | ---: | --- | --- |
| Paperclip | 2026.831.1 | 2026.916.0 | The candidate defaults `instance_settings.experimental.enableNativeRunner` to true. No supported narrow self-hosted control preserves explicit user choices; managed config changes deployment semantics, and `onboard --yes` starts in the foreground before wrapper postprocessing. | Upstream-supported self-hosted default control plus preserved explicit settings and fresh, upgrade, and native validation |
| TypeScript | 6.0.3 | 7.0.2 | TypeScript 7 removes the current programmatic API and replaces the tsserver interface. [TypeScript 7 release](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/) | Deliberate API/LSP or side-by-side design plus compiler import, `tsc`, and editor/server fixtures |
| Prisma | 7.10.0 | 8.0.0-rc.15 | Direct release candidate excluded | Stable 8.x plus database, client, migration, and owner-scoped replacement fixtures |
| json-server | 0.17.4 | 1.0.0-beta.15 | Direct beta excluded | Stable 1.x plus CLI and CRUD fixtures |
| PM2-owned js-yaml | 4.3.2 | 5.4.2 | Owner declares v4; replacing it crosses a major | Owner/API checks and PM2 YAML fixture |
| Paperclip-owned Undici | 6.28.1 | 8.10.2 | Replacement crosses two majors beyond the held Paperclip graph | Owner, streaming, error, and request fixtures |
| pydantic-core | 2.46.5 | Newer registry release | Exact Pydantic owner constraint | Pydantic selects a newer compatible core |
| pyee | 13.0.1 | 14.x | Playwright requires `<14` | Playwright widens its supported range and consumer checks pass |

`opencode-claude-auth 2.2.0` remains the current published plugin and issue #11 remains unresolved. This release does not claim an authentication fix. The reported proactive refresh and expired-credential errors still require upstream correction; running `claude` or signing in again remains a workaround, not proof that the race is fixed.

Claude Code synthetic-auth startup and marketplace/path-containment regression coverage are required release gates through `scripts/smoke_image.sh`; no live account, provider, OAuth, or billing claim follows from those fixtures.

Paperclip 2026.831.1 is unchanged from v1.2.1, so v1.2.2 adds no Paperclip migration, announcements override, managed-mode switch, or native-runner default override. Untouched v1.2.1 volume backups remain the rollback boundary.

## Notices and installed evidence

The selected preflight AMD64 image inventory contained 1,296 npm instances, 57 Python distributions, and 508 Debian packages. Its changed-package notice evidence includes:

| Component | Selected evidence |
| --- | --- |
| OpenCode 1.18.31 | Installed MIT license file |
| Claude Code 2.1.276 | Registry tarball, installed CLI, and Linux x64 native payload carry the same 147-byte legal-agreements notice; keep `SEE LICENSE`, not a permissive SPDX label |
| OpenSpec 1.13.1 | Installed MIT license file |
| pnpm 12.4.2 | Manifest declares MIT; no package-root license file in the selected image |
| Prettier 3.9.8 | Installed MIT license file |
| Wrangler / Miniflare / workerd | Manifests declare `MIT OR Apache-2.0`, MIT, and Apache-2.0; no package-root license files in the selected image |
| GitHub CLI 2.101.0 | Exact upstream source commit and MIT license |
| Playwright 1.63.0 | Apache-2.0 distribution and driver notice set; uses system Chromium |
| pandas 3.0.6 | Installed license file includes the primary license plus bundled third-party texts |

`THIRD-PARTY-NOTICES` records these boundaries without claiming legal clearance. The final native images must prove that the installed notice bytes and architecture-specific packages match the release source.

## Security and CI signals

The source suite currently passes 84 tests. Workflow pin validation passes with Renovate 44.97.6 and the updated immutable Docker action commits. Scanner parsers reject malformed and cross-scanner reports through their invalid-report path.

Selected preflight AMD64 scans are not the final native release scans. Their High/Critical records are unfixed Debian findings rather than Node, Python, or Go findings, and the fixable High/Critical policy replay passed. The preflight still contains unfixed distro risk and does not mean the image has zero vulnerabilities. Final notice-bound AMD64 and ARM64 scans, advisory review, and policy replay remain release gates.

Official Debian tracking confirms three preflight Critical records without a fixed Trixie package: [CVE-2026-6653](https://security-tracker.debian.org/tracker/CVE-2026-6653) affects the installed libxml2 runtime parser, [CVE-2026-60002](https://security-tracker.debian.org/tracker/CVE-2026-60002) affects the outbound OpenSSH client, and [CVE-2026-43185](https://security-tracker.debian.org/tracker/CVE-2026-43185) applies to installed `linux-libc-dev` headers rather than a running kernel or package runtime. Debian's `no-dsa` or minor classification is not proof of safety. The release keeps the default Trixie suite, adds no exception, and does not mix backports or sid packages.

## Release gates still pending

Publication requires all of the following on the exact notice-bound candidate:

1. Native AMD64 and native ARM64 build and complete smoke execution, including system Chromium with Playwright 1.63.0.
2. Runtime/plugin modes and exact v1.2.1 upgrade, restart, untouched-volume rollback, listener, and outbound/provider activation checks.
3. Installed inventory and `THIRD-PARTY-NOTICES` byte equality on both architectures.
4. Per-platform SBOM, provenance/attestations, Trivy and Docker Scout reports, policy replay, and release-asset checksums.
5. One direct `main` release commit, tag, and GitHub release named `v1.2.2`, followed by exact Docker Hub/GHCR alias and digest verification.

Any image-affecting or notice-affecting edit invalidates earlier candidate evidence. This audit does not claim the release has shipped.
