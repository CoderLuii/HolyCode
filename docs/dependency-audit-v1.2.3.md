# HolyCode v1.2.3 Dependency Audit

Date: 09/24/2026

Git predecessor `v1.2.2` is the supported release baseline. Upgrade and rollback validation uses `coderluii/holycode:1.2.2@sha256:b3a7e4f6d71c57db2b90b90a5e5cd011117da7567369cf3de5c44a1d78e4ade6`.

This audit records the selected v1.2.3 source graph. It is not a publication record. The notice-bound candidate still needs final native AMD64 and ARM64 builds, installed-notice equality, complete runtime/plugin and upgrade/rollback checks, per-platform SBOM and provenance, scanners, artifact checksums, and registry alias verification for the exact release digest.

## Selected updates

| Component | v1.2.2 | v1.2.3 | Decision and source |
| --- | --- | --- | --- |
| Node.js base | `24.21.0-trixie-slim@sha256:d7b4e5c4ad20b327d7bb16fab6aecd60ac20aa50f8514eb75a2b059e89abe48e` | `24.21.0-trixie-slim@sha256:8ec5d7557396cfe32d21c3f9c13072355ceab22b584578ca4bb28af31120cffe` | Same Node 24 LTS release with a refreshed official OCI index; rebuild and scan required. [Official image](https://hub.docker.com/_/node) |
| Go builder base | `1.27.1-trixie@sha256:9baa6b4187bbb98d240372a8a235ac0bb6b5ddd52bba1431dc2f7c0705862728` | `1.27.1-trixie@sha256:433790e515d27dc6003e847e644cc0af956985cf315c1c58a3b73ee2dd305183` | Same Go release with a refreshed official OCI index; all three source-builder stages use the same pin. [Official image](https://hub.docker.com/_/golang) |
| OpenCode | 1.18.31 | 1.18.32 | Exact npm package selected; lifecycle and native payload checks remain image gates. [Registry](https://registry.npmjs.org/opencode-ai/1.18.32) |
| Claude Code | 2.1.276 | 2.1.281 | Exact npm package selected; synthetic-auth startup and installed legal-notice equality remain image gates. [Registry](https://registry.npmjs.org/@anthropic-ai%2fclaude-code/2.1.281) |
| OpenSpec (`@fission-ai/openspec`) | 1.13.1 | 1.13.2 | Telemetry stays disabled and project initialization stays explicit. [Registry](https://registry.npmjs.org/@fission-ai%2fopenspec/1.13.2) |
| `opencode-claude-auth` | 2.2.0 | 2.2.1 | Exact offline plugin payload selected. This update is not evidence that issue #11 is fixed. [Registry](https://registry.npmjs.org/opencode-claude-auth/2.2.1) |
| npm | 12.0.2 | 12.1.0 | Direct CLI update with the reviewed owner-scoped replacement graph retained. [Registry](https://registry.npmjs.org/npm/12.1.0) |
| tsx | 4.23.13 | 4.23.15 | Direct stable update. [Registry](https://registry.npmjs.org/tsx/4.23.15) |
| pnpm | 12.4.2 | 12.6.0 | Exact package selected; lifecycle scripts remain blocked and offline execution remains an image gate. [Registry](https://registry.npmjs.org/pnpm/12.6.0) |
| Vite | 8.3.0 | 8.3.1 | Direct stable update with the existing esbuild boundary retained. [Registry](https://registry.npmjs.org/vite/8.3.1) |
| Prettier | 3.9.8 | 3.9.9 | Direct stable update. [Registry](https://registry.npmjs.org/prettier/3.9.9) |
| Lighthouse | 13.4.1 | 13.5.0 | Direct stable update; the global npm diagnostic remains owner- and version-bound. [Registry](https://registry.npmjs.org/lighthouse/13.5.0) |
| Wrangler | 4.134.0 | 4.138.0 | Exact package selected with its owner-declared Miniflare `5.20260921.1-alpha` and workerd `1.20260921.1` graph. [Registry](https://registry.npmjs.org/wrangler/4.138.0) |
| ESLint | 10.10.0 | 10.11.0 | Direct stable update. [Registry](https://registry.npmjs.org/eslint/10.11.0) |
| drizzle-kit | 0.31.10 | 0.31.11 | Direct global CLI update. [Registry](https://registry.npmjs.org/drizzle-kit/0.31.11) |
| Drizzle ORM fixture | 0.45.2 | 0.45.3 | Test-fixture update only; it does not add a new top-level image dependency. [Registry](https://registry.npmjs.org/drizzle-orm/0.45.3) |
| Renovate validator | 44.97.6 | 44.112.3 | CI-only exact version; it is not bundled in the runtime image. [Registry](https://registry.npmjs.org/renovate/44.112.3) |

## Direct image tools

These are the direct versioned tools and runtimes selected by the Dockerfile. `Current` means the reviewed stable selection did not change in v1.2.3; it does not promise that a mutable registry tag will never move.

| Tool or runtime | Selected version | Outcome |
| --- | ---: | --- |
| Node.js / npm | 24.21.0 / 12.1.0 | Node digest refreshed; npm updated |
| Python / pip / setuptools | 3.13 / 26.2.1 / 84.0.0 | Compatibility hold; direct and transitive lock graph unchanged |
| Go builder | 1.27.1 | Digest refreshed; release unchanged |
| GitHub CLI | 2.101.0 | Current, unchanged |
| OpenCode | 1.18.32 | Updated |
| Claude Code | 2.1.281 | Updated |
| Paperclip | 2026.831.1 | Compatibility hold; details below |
| OpenSpec | 1.13.2 | Updated |
| `opencode-claude-auth` | 2.2.1 | Updated without an issue #11 fix claim |
| TypeScript | 6.0.3 | Compatibility hold; details below |
| PM2 | 7.0.4 | Current, unchanged |
| tsx | 4.23.15 | Updated |
| pnpm | 12.6.0 | Updated |
| Vite | 8.3.1 | Updated |
| Prettier | 3.9.9 | Updated |
| Prisma | 7.10.0 | Stable hold; details below |
| drizzle-kit | 0.31.11 | Updated |
| Lighthouse | 13.5.0 | Updated |
| Wrangler / Miniflare / workerd | 4.138.0 / 5.20260921.1-alpha / 1.20260921.1 | Updated as one owner-bound graph |
| ESLint | 10.11.0 | Updated |
| s6-overlay | 3.2.3.2 | Current, unchanged |
| delta / eza | 0.19.2 / 0.23.5 | Current, unchanged |
| fzf / lazygit | 0.74.4 / 0.65.1 | Current source builds from pinned upstream commits |
| json-server | 0.17.4 | Stable hold; details below |
| Chromium | Debian Trixie package | Distro-managed; exact final package version belongs to the release SBOM |

Hermes and HolyCode-managed oh-my-openagent installation remain suspended. CLIProxyAPI remains an externally managed endpoint, not a bundled sidecar. Netlify CLI, `serve`, Vercel, sharp-cli, concurrently, and LHCI remain outside the image.

## Python lock hold

The direct Python inputs and both complete hash locks remain unchanged from v1.2.2. The selected set still includes Playwright 1.63.0, pandas 3.0.6, NumPy 2.5.3, Matplotlib 3.11.2, FastAPI 0.141.1, and Uvicorn 0.53.0.

The accepted locks were generated with Python 3.13.15, pip 26.2.1, pip-tools 7.6.1, and resolver-only Click 8.4.2. Product `click==8.5.0` remains unchanged.

pip-tools 7.6.1 still writes a false `--no-index` header when its updater environment resolves Click 8.5.0. Upstream issue [#2472](https://github.com/jazzband/pip-tools/issues/2472) and fix PR [#2475](https://github.com/jazzband/pip-tools/pull/2475) remain unreleased. Automatic pip-tools lock updates are therefore still blocked. HolyCode does not ship a fabricated header, product downgrade, or local updater workaround.

## Owner-scoped graph and replacement inventory

These versions are not independent top-level tool claims. Each stays inside the named owner boundary and is checked against that owner's declared graph or HolyCode's reviewed raw replacement.

| Owner boundary | Selected component | Outcome and rationale |
| --- | --- | --- |
| npm 12.1.0 / minimatch | `brace-expansion` 5.0.12 | Existing raw npm payload retained inside the accepted owner range |
| npm 12.1.0 | `tar` 7.5.22 | Existing raw replacement retained |
| npm 12.1.0 / socks | `ip-address` 10.7.2 | Existing raw npm payload retained inside the accepted owner range |
| PM2 7.0.4 | `js-yaml` 4.3.2 | Existing v4-compatible raw replacement retained; 5.x remains a major-boundary hold |
| Paperclip 2026.831.1 | Undici 6.28.1 | Existing owner-compatible replacement retained; 8.x crosses two majors |
| Paperclip 2026.831.1 | embedded PostgreSQL 18.1.0-beta.16 native packages | Existing architecture-specific lifecycle entries retained |
| Prisma 7.10.0 | deepmerge-ts 8.0.2, mysql2 3.24.4 | Existing owner-scoped replacements retained |
| Prisma / mysql2 | `@types/node` 20.19.43, `undici-types` 6.21.0 | Existing type-only peer and declaration payloads retained |
| Wrangler 4.138.0 | Miniflare 5.20260921.1-alpha, workerd 1.20260921.1 | Exact versions declared by Wrangler; workerd is not an independent latest pin |
| Miniflare | Sharp 0.35.4 and libvips 1.3.3 | Existing owner graph retained and byte-checked in image validation |
| pip 26.2.1 | vendored msgpack 1.2.2 | Existing hash-verified vendor replacement retained |
| pip 26.2.1 | pkg_resources from setuptools 78.1.1 | Existing checksum-verified vendor replacement retained |

Prisma's type-only peer remains @types/node 20.19.43 with undici-types 6.21.0 beside it. Both stay inside Prisma's package scope and are not new top-level runtime tools.

Drizzle ORM 0.45.3 is a fixture-only compatibility dependency. It verifies the globally installed drizzle-kit 0.31.11 consumer path without turning Drizzle ORM into a new top-level HolyCode tool.

The complete global npm diagnostic remains bounded to two accepted owner findings. Lighthouse 13.5.0 owns `@paulirish/trace_engine 0.0.65`, whose literal latest declarations resolve to `third-party-web 0.30.0` and `legacy-javascript 0.0.1`. Missing peers or any changed or additional finding fail the smoke. This is not a universal clean-tree claim.

Paperclip's packaged catalog remains package data. The held package contains 16 local entries with 27 verified local files plus one optional pinned remote descriptor with 79 metadata records. HolyCode does not materialize those remote records in user-managed configuration during image smoke.

## Compatibility holds and unresolved items

| Component | Retained | Evaluated alternative | Why it remains held | Unlock condition |
| --- | ---: | ---: | --- | --- |
| Paperclip | 2026.831.1 | 2026.916.1 | The latest patch changes task-conversation messaging, not the 2026.916.0 native-runner default. The candidate enables the runner by default for explicitly configured agents, and no supported narrow self-hosted control preserves explicit user choices. | Upstream-supported self-hosted default control plus preserved explicit settings and fresh, upgrade, and native validation |
| TypeScript | 6.0.3 | 7.0.2 | TypeScript 7 removes the current programmatic API and replaces the tsserver interface. | Deliberate API/LSP or side-by-side design plus compiler import, `tsc`, and editor/server fixtures |
| Prisma | 7.10.0 | 8.0.0-rc.15 | Direct release candidate excluded. | Stable compatible 8.x plus database, client, migration, and owner-scoped replacement fixtures |
| json-server | 0.17.4 | 1.0.0-beta.15 | Direct beta excluded. | Stable 1.x plus CLI and CRUD fixtures |
| PM2-owned js-yaml | 4.3.2 | 5.4.2 | Owner declares v4; replacing it crosses a major. | Owner/API checks and PM2 YAML fixture |
| Paperclip-owned Undici | 6.28.1 | 8.10.2 | Replacement crosses two majors beyond the held Paperclip graph. | Owner, streaming, error, and request fixtures |
| Python lock graph | v1.2.2 direct and transitive locks | New resolver output | The upstream pip-tools header correction is not released. | Released upstream fix plus clean supported Linux regeneration and consumer validation |

`opencode-claude-auth 2.2.1` is selected, but issue [#11](https://github.com/CoderLuii/HolyCode/issues/11) remains open. The release note for 2.2.1 does not establish a correction for the reported proactive refresh and expired-credential failure. Running `claude` or signing in again remains a workaround, not proof that the race is fixed.

Claude Code synthetic-auth startup and marketplace/path-containment regression coverage are required release gates through `scripts/smoke_image.sh`; no live account, provider, OAuth, or billing claim follows from those fixtures.

Paperclip 2026.831.1 is unchanged from v1.2.2, so v1.2.3 adds no Paperclip migration, announcements override, managed-mode switch, or native-runner default override. Untouched v1.2.2 volume backups remain the rollback boundary.

## CLIProxyAPI model discovery

Issue [#12](https://github.com/CoderLuii/HolyCode/issues/12) reported that an enabled external CLIProxyAPI provider could start without models when no explicit model configuration was supplied. The v1.2.3 source candidate adds bounded, redirect-free discovery from the configured endpoint's `/v1/models` response. An explicit `CLIPROXYAPI_MODELS` allowlist skips discovery. The implementation preserves the separate `cliproxyapi` provider and does not change Claude Auth configuration or files.

This is source-level candidate behavior, not release evidence. Native image validation still must cover one, multiple, zero, malformed, unauthorized, unreachable, and explicit-override cases without leaking credentials or blocking startup indefinitely.

## Notices and installed evidence

`THIRD-PARTY-NOTICES` records the changed redistributed packages and retained owner boundaries without claiming legal clearance. The final native images must prove that installed notice bytes, package versions, and architecture-specific payloads match the selected source graph on AMD64 and ARM64.

Renovate 44.112.3 is CI-only and is not listed as a redistributed runtime component. The Drizzle ORM 0.45.3 fixture is test-only and is not copied into the image.

## Security and CI signals

Local source tests and policy validators are necessary candidate checks, not native release proof. Final notice-bound AMD64 and ARM64 scans, advisory review, and fixable High/Critical policy replay remain release gates. The release keeps the default Debian Trixie suite, adds no scanner exception, and does not claim zero vulnerabilities.

## Release gates still pending

Publication requires all of the following on the exact notice-bound candidate:

1. Native AMD64 and native ARM64 build and complete smoke execution, including CLIProxyAPI model discovery and system Chromium with Playwright 1.63.0.
2. Runtime/plugin modes and exact v1.2.2 upgrade, restart, untouched-volume rollback, listener, and outbound/provider activation checks.
3. Installed inventory and `THIRD-PARTY-NOTICES` equality on both architectures.
4. Per-platform SBOM, provenance/attestations, Trivy and Docker Scout reports, policy replay, and release-asset checksums.
5. One direct `main` release commit, tag, and GitHub release named `v1.2.3`, followed by exact Docker Hub/GHCR alias and digest verification.

Any image-affecting or notice-affecting edit invalidates earlier candidate evidence. This audit does not claim the release has shipped.
