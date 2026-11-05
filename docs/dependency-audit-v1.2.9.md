# HolyCode v1.2.9 Dependency Audit

Date: 11/04/2026

The release predecessor is `v1.2.8`. Upgrade and rollback checks use `coderluii/holycode:1.2.8@sha256:e3b53026050ef69998045f273f01f13131e5f7b6e52d5e9978e7ea26c68133da`, the verified Docker Hub and GHCR index.

This records the selected source graph. It does not establish publication, native runtime verification, or deployment. Release assets must identify the exact image digests, native architecture results, full scanner reports, inventories, SBOMs and build provenance.

## Selected official updates

| Component | v1.2.8 | v1.2.9 selection | Required verification |
| --- | --- | --- | --- |
| Node.js | 24.22.1 | 24.22.2, official Trixie slim index | Both native architectures, runtime and package-manager consumers |
| Chromium/common/sandbox | Floor 155.0.8059.79-1~deb13u1 | Floor 156.0.8078.79-1~deb13u1, official Debian security packages | Fresh repository resolution, sandbox and browser checks, final-image inventories/scans |
| OpenCode / Claude Code | 1.19.3 / 2.1.307 | 1.19.5 / 2.1.318 | Official integrity, lifecycle policy, native startup and plugin modes |
| npm / pnpm | 12.2.1 / 12.15.0 | 12.2.2 / 12.16.1 | Official published graphs, native-addon/download and offline-workspace fixtures |
| PM2 | 7.0.4 with local owner replacements | Official 7.1.2 | YAML/process-supervision fixtures and resolved owner graph |
| Wrangler | 4.151.3 | 4.157.0 | Published Miniflare 5.20261103.0-beta, workerd 1.20261103.1, Sharp 0.35.5 and esbuild 0.28.2 graph |
| Lighthouse | 13.5.0 | 13.6.0 | Published trace-engine 0.0.67, third-party-web resolution, clean npm tree and CLI fixtures |
| GitHub CLI | 2.103.0 | 2.103.3 | Official per-architecture archive checksums and version checks |
| Paperclip-owned Cursor SDK | 1.0.40 | 1.3.1 through the existing `^1.0.28` declaration | Published integrity, API/type exports, missing-key diagnostics and native owner graph; Paperclip 2026.831.1, jsdom 30.1.3 and Undici 8.12.3 stay unchanged |
| Python Playwright / Certifi | 1.64.0 / 2026.10.19 | 1.64.1 / 2026.10.23 | Linux Python 3.13 hash locks, system Chromium and TLS consumers |
| pip | 26.2.2 with vendor repairs | Official 26.3 wheel and offline seed | Wheel integrity, vendor RECORD, legacy metadata, HTTP/TLS/proxy and offline-seed consumers |
| Docker Scout | 1.27.0 | 1.29.0 | Official architecture checksums, full/fixable reports, package identities and result-to-PURL accounting |
| docker/login-action | 4.6.0 | Immutable 4.7.0 commit | Workflow pin validation; existing repository access controls stay active |

The source uses official upstream packages. Do not modify third-party package code or manifests to force these versions. Registry integrity, declared owner ranges and actual consumer behavior are separate checks.

## Retired dependency repairs

npm 12.2.2 supplies node-gyp 13.0.0 and Undici 6.29.1 through its official bundle. The old node-gyp/Undici replacement is retired. Keep the download and native-addon compilation/load fixtures; a version comparison alone does not establish compatibility.

PM2 7.1.2 declares js-yaml 4.3.2 itself. Its published graph no longer contains the old get-uri/basic-ftp subtree. Both owner replacements are retired; keep YAML and process-supervision checks. Historical direct FTP fixtures do not establish a requirement to add a removed dependency back into PM2.

pip 26.3 supplies msgpack 1.2.4, urllib3 2.8.0 and Certifi 2026.10.23. Its official setuptools/pkg_resources payload remains 70.3.0. The image uses the unmodified official wheel and seed rather than rebuilding vendored code. Keep RECORD, legacy metadata, msgpack, HTTP/TLS/proxy and offline-seed checks. Known upstream vulnerabilities remain advisory under the policy below; removing a repair is not a claim that its old advisory has disappeared.

Lighthouse 13.6.0 removes legacy-javascript from the selected trace-engine graph. Resolve third-party-web through the official declaration, verify the exact tree and run the consumers. Historical repair artifacts remain historical records; they are not newly applied patches.

## Security delivery policy

Run Trivy 0.76.1 and Docker Scout 1.29.0 on each exact native candidate image. Retain complete Critical/High, fixable and secret reports, package inventories and SPDX. Keep normalized finding counts separate from unique vulnerability IDs and preserve raw repeated observations.

Known third-party dependency findings are advisory when the report identifies the actual upstream package, installed version, vulnerability identity and provenance. Record accepted upstream findings with their evidence and do not describe them as fixed, unreachable or safe. Such findings alone do not block this approved maintenance release. Project-owned findings, secrets, missing or malformed reports, ambiguous package association and scanner execution failures remain blocking.

Scout's package-identity changes can alter accounting without fixing a package vulnerability. Retain the existing result-to-package/PURL guards and distinguish accounting changes from actual dependency fixes. Do not suppress raw findings or claim a zero-vulnerability image.

Keep the non-root runtime, Chromium sandbox, supplied seccomp profile and closed browser port. Avoid untrusted browser content and automation while known findings remain. Use official Debian Chromium packages; do not custom-build or patch the browser.

Chromium issue #14 was closed against verified v1.2.8 native release evidence. Keep that historical result intact. New findings need their own source/image-bound evidence; a package-version increase does not prove resolution.

## Compatibility holds

| Component | Decision |
| --- | --- |
| Paperclip 2026.831.1 | Preserve service behavior, integrations, user data and the native-runner default. Newer releases need a copied-data migration and untouched-snapshot rollback. |
| Claude Auth 2.2.1 | Version 3 targets OpenCode 2 and changes the configuration contract. Issue #11 closed after the reporter switched plugins; no original-path token-refresh fix is claimed. |
| TypeScript 6.0.3 | Preserve the stable programmatic API and tsserver feature; TypeScript 7 needs a separate migration. |
| json-server 0.17.4 | Keep stable behavior instead of adopting the 1.0 beta. |
| Apprise 1.13.1 | Keep notifier/API compatibility; defer the 2.x migration. |
| Hermes / managed oh-my-openagent | Managed availability remains suspended. Preserve existing data, settings, skills and caches. |
| Prisma 7.10.1 | Keep stable v7 rather than an 8.0 release candidate. |

Provider credentials, Claude configuration, external CLIProxyAPI endpoints and persistent paths remain user-owned. Offline fixtures do not establish authenticated provider, OAuth or account behavior. The older local Codex/Gemini/ttyd feature branch remains separate; it is not merged into dependency maintenance.

## Local checks and delivery gates

Run source checks before the direct-main commit: Python unittest discovery, workflow-pin and seccomp validators, JSON/YAML and both Compose configurations, and Renovate 44.129.0 extraction under Node 24.22.2. Preserve lifecycle policy, official package-owner, native-addon, PM2, Python, Paperclip, Drizzle, plugin and browser fixtures.

Loopback TLS/proxy fixtures use explicit IPv4 addresses and test hostname rejection through SNI, so IPv6 fallback cannot consume the request budget. Certificate trust, mutual TLS, proxy isolation and the oversized-chunk timing check remain required.

Build and validate artifacts against the final release commit. Require native AMD64 and native ARM64 smoke/plugin checks, both full scanner gates and upgrade/untouched-volume rollback from the pinned predecessor. Local emulation is separate evidence and does not replace native ARM64. Use bounded task-owned resources; never prune shared Docker resources or alter its memory limit to run a check.

Publish only the exact validated candidate. Preserve per-platform SPDX and maximum BuildKit provenance, VCS source/revision and Dockerfile identity. Record the real local builder origin when local delivery is used; do not fabricate GitHub execution metadata or signatures. The project does not configure image signing.

Use one direct-main commit titled `v1.2.9`, with `v1.2.8` as its sole release predecessor. The tag and GitHub release title must match. Do not create a release PR, move an existing tag or overwrite immutable release assets. Preserve repository access controls and all validation requirements. Record a failed release/deployment step, cause, correction and prevention check before retrying.

Verify Docker Hub and GHCR version/latest aliases, both platform manifests and attestations against the validated index. Retain the published architecture evidence and release checksums. Accepted upstream findings and unavailable checks must remain explicit.

## Website follow-up

The associated website is maintained in `CoderLuii/holycode-site`. Its Astro 7.4.5 and Tailwind 4.3.4 maintenance is independent of image publication. Keep website release facts at v1.2.8 until v1.2.9 is actually published, then synchronize versions, installer output, history and security wording from the tagged product source. Run all README commands, headless browser/accessibility checks and schema/content parity before a separate Pages deployment. Verify the immutable deployment and public domain against the same build. Product publication alone does not establish website deployment.
