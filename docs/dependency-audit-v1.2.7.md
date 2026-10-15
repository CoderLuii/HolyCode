# HolyCode v1.2.7 Dependency Audit

Date: 10/14/2026

The release predecessor is `v1.2.6`. Upgrade and rollback checks use `coderluii/holycode:1.2.6@sha256:42233ec8c9d3ba32f17edb1bbf90dcf38694a39c65b1216146994f1ca85b25d7`, the verified Docker Hub and GHCR index.

This records the selected source graph. It does not establish publication or native runtime verification. The final workflow and release assets identify the exact images, native results, scanner records, SBOMs and provenance.

## Selected official updates

| Component | v1.2.6 | v1.2.7 selection | Verification |
| --- | --- | --- | --- |
| Node LTS | 24.21.0 | 24.22.0 | Official dual-platform Trixie-slim digest, runtime and complete base graph |
| Chromium / common / sandbox | 154.0.8037.92-1~deb13u1 | At least 155.0.8059.39-1~deb13u1 | Official Trixie security packages, both native architectures, sandbox and fresh scans |
| fzf / lazygit | 0.74.4 / 0.66.0 | 0.74.5 / 0.66.1 | Official release archives and checksums |
| OpenCode | 1.18.35 | 1.19.0 | Official npm integrity, lifecycle policy, platform payload and startup |
| Claude Code | 2.1.296 | 2.1.300 | Integrity, lifecycle policy, native startup and marketplace containment |
| OpenSpec | 1.14.1 | 1.14.2 | Offline initialization, validation and archive fixture |
| pnpm / Prettier | 12.10.1 / 3.9.9 | 12.11.2 / 3.9.10 | Official integrity, disabled lifecycle scripts and CLI fixtures |
| Wrangler | 4.149.0 | 4.151.0 | Owner graph with Miniflare 5.20261012.0-beta and workerd 1.20261012.1 |
| Playwright | 1.63.0 | 1.64.0 | Python 3.13 hash lock, native browser and hidden-iframe visibility fixtures |
| NumPy / Markdown / FastAPI | 2.5.3 / 3.11 / 0.143.0 | 2.5.4 / 3.11.1 / 0.143.1 | Clean hash-locked Python installation, imports and application fixtures |
| setup-node / upload-artifact | 7.0.0 / 7.0.1 | 7.1.0 / 7.0.2 | Official immutable action commits and workflow contracts |
| Trivy | 0.75.0 | 0.76.0 | Architecture-specific official checksums, full vulnerability and secret reports |

Package metadata comes from the official [npm registry](https://registry.npmjs.org/) and [PyPI](https://pypi.org/). Python locks use official pip-tools 7.6.2 under Linux Python 3.13, matching the image runtime. Resolve platform markers in Linux rather than copying a Windows-only dependency graph. Do not add a manual workaround or extend pip vendor repairs.

Paperclip 2026.831.1 keeps its normal Cursor SDK 1.0.37 and jsdom 30.1.2 graph. jsdom's unchanged `undici ^8.11.2` declaration now resolves official Undici 8.12.1. Verify the fresh owner resolution before building; do not replace or patch SDK code.

Lighthouse trace graph: Lighthouse 13.5.0 keeps `@paulirish/trace_engine` 0.0.65 and `third-party-web` 0.30.0. Its unchanged `legacy-javascript: latest` declaration now selects 0.0.3. Exact normal-owner graph checks and expected/actual diagnostics remain required. No third-party code or manifests are changed.

Wrangler owns its Miniflare/workerd selection. Keep its official Sharp 0.35.5/libvips 1.3.4 graph rather than independently selecting a newer Miniflare distribution tag.

Debian packages resolve from current official Trixie repositories at build time. Refreshing the apt layer is not a promise of byte-for-byte reproducibility. Ubuntu workflow jobs stay on 24.04.

## Security delivery policy

Trivy and Docker Scout keep their full Critical/High reports. Findings with verified third-party package provenance are recorded by dependency, installed version and vulnerability ID as accepted upstream vulnerabilities. Acceptance permits delivery; it does not mean the vulnerability is fixed, unreachable or safe. Secret findings, HolyCode-owned findings, unknown package provenance, invalid or missing reports, and scanner execution failures still block release.

The published v1.2.6 images contain Chromium `154.0.8037.92-1~deb13u1`. Official Debian Trixie security now provides matching Chromium, common and sandbox packages `155.0.8059.39-1~deb13u1` for AMD64 and ARM64. The [Debian tracker](https://security-tracker.debian.org/tracker/source-package/chromium) marks CVE-2026-103622, CVE-2026-103624, CVE-2026-103625, CVE-2026-103626, CVE-2026-103628, CVE-2026-106195 and CVE-2026-106237 fixed at this version. Package availability is not proof about a rebuilt or published HolyCode image.

The previous ARM64 package exception is no longer used. Earlier images still need an upgrade. Fresh release scans determine the current advisory inventory; the seven named CVEs are not a complete inventory of possible future findings. Avoid untrusted browser content and automation while known findings remain. Keep the sandbox, seccomp profile, non-root user and closed browser port. These controls do not establish that the flaws are unreachable. Do not patch or custom-build Chromium.

Close [issue #13](https://github.com/CoderLuii/HolyCode/issues/13) only after corrected Chromium/Common/Sandbox packages on both architectures, native browser smokes, fresh Scout and Trivy results clearing all seven named CVEs, registry aliases and updated public warnings are verified. Keep any other Chromium findings explicitly tracked before closing. Accepted vulnerabilities are not verified fixes.

## Compatibility holds

| Component | Decision |
| --- | --- |
| Paperclip 2026.831.1 | Preserve existing service behavior, integrations and data. Available 2026.1012.0 changes restore locking, authorization and database migrations; it requires a separate controlled migration and untouched-data rollback exercise, including legacy Composio connections and PostgreSQL hydration. |
| TypeScript 6.0.3 | Keep the stable programmatic API and tsserver feature. TypeScript 7 needs a separate integration migration. |
| Prisma 7.10.0 / json-server 0.17.4 | Keep stable releases rather than Prisma 8 RC or json-server 1 beta. |
| Apprise 1.13.1 | Defer the 2.0 major change until notifier/API compatibility is tested. |
| Existing npm/PM2 owner replacements | Preserve the current graph. New ip-address, node-gyp, basic-ftp and js-yaml replacements must not extend manual third-party modifications. Use an official owner release or verified normal resolution first. |
| Existing pip vendor repairs | Preserve released behavior without adding patches, forks, custom builds or extended vendored fixes. |
| Claude Auth 2.2.1 | Current official release; no credential-refresh fix is established. [Issue #11](https://github.com/CoderLuii/HolyCode/issues/11) needs original-path idle-expiry reproduction and verified recovery through restart. |

OpenSpec (`@fission-ai/openspec` 1.14.2) stays pinned with telemetry disabled. Its offline fixture covers explicit initialization, change validation and archive behavior.

The Claude marketplace containment fixture must pass on both native architectures. It does not establish a live account, provider, OAuth, or billing result.

External CLIProxyAPI endpoints, explicit models and user-owned providers remain supported. They do not establish a Claude Auth fix. User-managed plugins and existing Hermes data remain preserved. Hermes service and HolyCode-managed oh-my-openagent installation stay suspended.

The local harness-agnostic feature work is outside this maintenance release. Its earlier evidence does not validate current source or Cloud workspace-count claims. Workspace provisioning, load tests, owner sign-off and localization remain separate work.

## Required release checks

Use one direct-main commit titled `v1.2.7`, with `v1.2.6` as its sole release predecessor. Require source tests, immutable workflow pins, JSON/YAML and Compose validation, Renovate extraction, lifecycle policy, installed inventories, native AMD64 and ARM64 image smokes and plugin modes, upgrade/rollback, complete scanner reports and accepted findings, SBOM and provenance.

After publication, verify release assets, Docker Hub and GHCR `1.2.7`/`latest` digests, both platform manifests and attestations, and website synchronization. Identify local, hosted, native and emulated results separately. An unavailable check is not a pass. Do not create a release PR, move published tags or reuse evidence after image-affecting changes.
