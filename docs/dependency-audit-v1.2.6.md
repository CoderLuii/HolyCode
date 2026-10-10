# HolyCode v1.2.6 Dependency Audit

Date: 10/10/2026

The release predecessor is `v1.2.5`. Upgrade and rollback checks use `coderluii/holycode:1.2.5@sha256:035b0d86aafd7cf52db7dbbbd9cb3ae53cc195a1aa0ab58843c2c2d3809eb9e3`, the verified Docker Hub and GHCR index.

This records the selected source graph. It does not establish publication or native runtime verification. The final workflow and release assets identify the exact images, native results, scanner records, SBOMs and provenance.

## Selected official updates

| Component | v1.2.5 | v1.2.6 selection | Verification |
| --- | --- | --- | --- |
| OpenCode | 1.18.34 | 1.18.35 | Official npm integrity, lifecycle policy, platform payload and startup |
| Claude Code | 2.1.290 | 2.1.296 | Official npm integrity, lifecycle policy, native startup and marketplace path checks |
| pnpm | 12.9.1 | 12.10.1 | Exact blocked lifecycle scripts and offline project fixture |
| Vite | 8.3.2 | 8.3.4 | Packaged CLI and fixture smoke |
| Wrangler | 4.147.0 | 4.149.0 | Its matching Miniflare/workerd graph, package integrity and native runtime |
| Sharp / libvips (Wrangler-owned) | 0.35.4 / 1.3.3 | 0.35.5 / 1.3.4 | Official owner metadata, native integrity and AVIF round-trip |
| Cursor SDK (Paperclip-owned) | 1.0.36 | 1.0.37 | Normal adapter range, official SRI, packaged API and missing-key checks |
| Lighthouse trace graph | trace engine 0.0.65 / third-party-web 0.30.0 / legacy-javascript 0.0.1 | trace engine 0.0.65 / third-party-web 0.30.0 / legacy-javascript 0.0.3 | Normal `latest` owner resolution, official SRI and exact npm-tree diagnostics |
| Drizzle ORM fixture | 0.45.3 | 0.45.4 | Locked offline database smoke |
| python-dotenv | 1.2.3 | 1.2.4 | Python 3.13 hash lock and imports |
| Markdown | 3.10.3 | 3.11 | Hash lock and rendering fixture |
| FastAPI | 0.141.1 | 0.143.0 | Hash lock, imports and application smoke |
| Uvicorn | 0.53.0 | 0.54.0 | Hash lock and application smoke |
| pip-tools (resolver only) | 7.6.1 | 7.6.2 | Official recorded-command and Click 8.5 corrections; clean supported Linux lock generation |

Package metadata comes from the official [npm registry](https://registry.npmjs.org/) and [PyPI](https://pypi.org/). [pip-tools 7.6.2](https://github.com/jazzband/pip-tools/releases/tag/v7.6.2) releases the fixes that previously blocked lock updates. Do not add a manual workaround or extend pip vendor repairs.

Fresh Paperclip 2026.831.1 resolution selects Cursor SDK 1.0.37 within its unchanged adapter range `^1.0.28`. Bind that actual graph; do not replace or patch SDK code. jsdom 30.1.2 and its Undici 8.11.2 remain unchanged.

Fresh Lighthouse 13.5.0 resolution keeps `@paulirish/trace_engine` 0.0.65 and `third-party-web` 0.30.0, while the trace engine's unchanged `legacy-javascript: latest` declaration now selects 0.0.3. The runtime guard requires that exact normal owner graph and prints the expected and actual graph when registry movement changes it. No dependency code is replaced or patched.

Node 24.21.0 and its immutable Trixie-slim image stay unchanged. Debian packages resolve from the current official Trixie repositories; the refreshed apt layer is not a promise of byte-for-byte reproducibility. The remaining floating Ubuntu workflow jobs are pinned to 24.04 to preserve the tested runner family.

## Security delivery policy

Trivy and Docker Scout continue to produce their full Critical/High reports. Findings with verified third-party package provenance are recorded as accepted upstream vulnerabilities. Acceptance permits delivery; it does not mean the vulnerability is fixed, unreachable or safe. Secret findings, HolyCode-owned findings, unknown package provenance, invalid or missing reports, and scanner execution failures still block release.

The published v1.2.5 images contain Chromium `154.0.8037.92-1~deb13u1` on AMD64 and ARM64. That version fixes the older v1.2.4 `.57` advisory set. Five newer CVEs remain tracked in [issue #13](https://github.com/CoderLuii/HolyCode/issues/13): CVE-2026-103622, CVE-2026-103624, CVE-2026-103625, CVE-2026-103626 and CVE-2026-103628, including two Critical findings. The [Debian tracker](https://security-tracker.debian.org/tracker/source-package/chromium) still lists `.92` in Trixie security at this review. Its advisory list has changed since the prior release; fresh scans determine this release's accepted findings. Do not treat the five-item issue as a complete current vulnerability inventory.

Use corrected official Debian packages when available. Avoid untrusted browser content and automation while the findings remain. Keep the sandbox, seccomp profile, non-root user and closed browser port. These controls do not establish that the flaws are unreachable. Do not patch or custom-build Chromium. Close #13 only after corrected Chromium/Common/Sandbox packages, both native browser smokes, fresh scanner results for its five CVEs, registry aliases and updated public warnings are verified.

## Compatibility holds

| Component | Decision |
| --- | --- |
| Paperclip 2026.831.1 | Keep existing service behavior, integrations and data. Newer releases need a separate verified migration, including legacy Composio connections and PostgreSQL hydration. |
| TypeScript 6.0.3 | Keep the stable programmatic API and tsserver feature; TypeScript 7 needs a separate integration migration. |
| Prisma 7.10.0 / json-server 0.17.4 | Keep stable releases rather than Prisma 8 RC or json-server 1 beta. |
| Apprise 1.13.1 | Defer the 2.0 major change until notifier/API compatibility is tested. |
| Existing npm/PM2 owner replacements | Preserve the current graph. New ip-address, node-gyp, basic-ftp and js-yaml replacements must not extend manual third-party modifications. Use an official owner release or verified normal resolution first. |
| Wrangler Sharp/libvips | Miniflare now owns Sharp 0.35.5, whose official native packages own libvips 1.3.4. Follow that normal upstream graph and verify integrity, ownership and AVIF support. No third-party code is modified. |
| Existing pip vendor repairs | Keep the released behavior. This maintenance does not add patches, fork dependencies, custom-build tools or extend vendored fixes. |
| Claude Auth 2.2.1 | Keep the official offline payload. The credential-refresh root cause remains unconfirmed; [issue #11](https://github.com/CoderLuii/HolyCode/issues/11) needs reproduction and verified recovery. |

OpenSpec (`@fission-ai/openspec` 1.14.1) remains pinned with telemetry disabled. Its offline fixture covers explicit initialization, change validation and archive behavior.

The Claude marketplace containment fixture must pass on both native architectures. It does not establish a live account, provider, OAuth, or billing result.

External CLIProxyAPI endpoints, explicit models and user-owned providers remain supported. They do not establish a Claude Auth fix. User-managed plugins and existing Hermes data remain preserved. Hermes service and HolyCode-managed oh-my-openagent installation stay suspended.

The local harness-agnostic feature work is outside this maintenance release. Its earlier evidence does not validate the current source or Cloud workspace-count claims.

## Required release checks

Use one direct-main commit titled `v1.2.6`, with `v1.2.5` as its sole release predecessor. Require source tests, immutable workflow pins, JSON/YAML and Compose validation, Renovate extraction, lifecycle policy, installed inventories, native AMD64 and ARM64 image smokes and plugin modes, upgrade/rollback, both scanner reports and accepted findings, SBOM and provenance.

After publication, verify release assets, Docker Hub and GHCR `1.2.6`/`latest` digests, both platform manifests and attestations, and website synchronization. Native and emulated evidence must be identified separately. An unavailable check is not a pass. Do not create a release PR, move published tags or reuse evidence after image-affecting changes.
