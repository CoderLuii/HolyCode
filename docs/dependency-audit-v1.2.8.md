# HolyCode v1.2.8 Dependency Audit

Date: 10/26/2026

The release predecessor is `v1.2.7`. Upgrade and rollback checks use `coderluii/holycode:1.2.7@sha256:b212036da5c9057e02e2b0680d66fd5164272d0c9e3ef82c1542589236bd1ed1`, the verified Docker Hub and GHCR index.

This records the selected source graph. It does not establish publication, native runtime verification, or deployment. Release assets and workflow evidence must identify the exact image digests, architecture results, scanner records, SBOMs, and provenance.

## Selected official updates

| Component | v1.2.7 | v1.2.8 selection | Verification |
| --- | --- | --- | --- |
| Node LTS | 24.22.0 | 24.22.1 | Official security release, dual-platform Trixie-slim index digest, runtime and base graph |
| Chromium / common / sandbox | At least 155.0.8059.39-1~deb13u1 | At least 155.0.8059.79-1~deb13u1 | Current official Trixie package on both native architectures, sandbox, browser smoke and fresh scans |
| GitHub CLI / lazygit | 2.102.0 / 0.66.1 | 2.103.0 / 0.66.2 | Official release archives and per-architecture checksums |
| OpenCode / Claude Code | 1.19.0 / 2.1.300 | 1.19.3 / 2.1.307 | Official npm integrity, lifecycle policy, native startup and marketplace containment |
| `@fission-ai/openspec` | 1.14.2 | 1.14.3 | Offline initialization, validation and archive fixture |
| Paperclip Cursor SDK | 1.0.37 | 1.0.40 within `^1.0.28` | Official npm integrity, runtime API, and Paperclip missing-key diagnostic; no Node transport |
| npm / pnpm | 12.2.0 / 12.11.2 | 12.2.1 / 12.15.0 | Official npm integrity, lifecycle policy, current owner graphs and CLI fixtures |
| Vite / ESLint | 8.3.4 / 10.12.0 | 8.3.5 / 10.13.0 | Isolated build and lint fixtures |
| Prisma | 7.10.0 with local replacements | 7.10.1 published graph | Official owner metadata, resolved graph, CLI and MySQL driver fixtures |
| Wrangler | 4.151.0 | 4.151.3 | Owner graph with Miniflare 5.20261019.1-beta, workerd 1.20261019.1, and Sharp 0.35.5 |
| Python stack | Playwright 1.64.0, Markdown 3.11.1, FastAPI 0.143.1, setuptools 84.0.0, Pillow 12.3.0, certifi 2026.7.22 | Playwright 1.64.0, Markdown 3.11.2, FastAPI 0.143.5, setuptools 84.2.1, Pillow 13.0.0, certifi 2026.10.19 | Linux Python 3.13 hash locks, clean image installation, and Pillow image encode/decode smoke |
| Trivy | 0.76.0 | 0.76.1 | Official per-architecture checksums and full vulnerability and secret reports |
| Docker Scout | 1.26.0 | 1.27.0 | Official AMD64 and ARM64 checksums; the release updates Go to 1.26.10 for security fixes |

The Playwright 1.64.1 candidate was not published on PyPI when checked, so the project keeps 1.64.0. Package metadata comes from the official [npm registry](https://registry.npmjs.org/) and [PyPI](https://pypi.org/). Python locks use pip-tools 7.6.2 under Linux Python 3.13, matching the image runtime. Platform markers are resolved in Linux rather than copied from a Windows dependency graph.

Pillow 13.0.0 is the official current release. Its removed APIs are not used by HolyCode code; the product uses the documented `Image.open`, conversion, and save APIs for image and headless screenshot checks. Keep those smoke checks as the compatibility gate. `certifi` 2026.10.19 is pinned directly so the application dependency graph receives the current official certificate bundle.

npm 12.2.1 now owns the dependency graph that previously needed HolyCode replacements for brace-expansion, tar, and ip-address. Its pre-overlay install currently resolves Undici 6.29.0; the image checks that graph before applying the separately integrity-pinned node-gyp 13.0.2 / Undici 8.12.3 compatibility replacement. Undici remains within node-gyp's declared `^8.4.1` range and meets the fixed 8.12.2 threshold for CVE-2026-109869. Keep the download/checksum and offline native-addon fixtures. Do not expand that patch; remove it only after an official npm owner graph makes it unnecessary and the native node-gyp fixtures pass. Official pnpm 12.15.0 bundles fixed Undici 6.29.1 without an overlay; retain the offline workspace and lifecycle-policy checks.

Prisma 7.10.1's published owner graph supplies deepmerge-ts 8.0.2 and mysql2 3.24.4. HolyCode no longer replaces those packages or materializes their type peers. The image checks the official owner declarations and resolved package versions, then exercises the CLI and MySQL driver.

Paperclip 2026.831.1 stays on its compatibility hold, but its declared Cursor SDK range `^1.0.28` now resolves to 1.0.40 (up from 1.0.37). The official package integrity and existing runtime and type API checks pass in Node 24.22.1. Paperclip's `cursor_cloud_api_key_missing` diagnostic also passes without credentials. SDK 1.0.40 no longer depends on `@connectrpc/connect-node`; Paperclip resolves jsdom 30.1.3, whose declared Undici range `^8.12.1` selects official Undici 8.12.3. This is a fresh owner graph, with no dependency replacement. This offline check does not prove authenticated Cursor API calls. Lighthouse trace graph: Lighthouse 13.5.0 keeps `@paulirish/trace_engine` 0.0.65 and `third-party-web` 0.30.0; the unchanged `legacy-javascript: latest` declaration now selects 0.0.4. Verify exact owner graphs and expected/actual diagnostics without editing third-party manifests or source.

10/25/2026 follow-up: the official [npm publication record](https://registry.npmjs.org/legacy-javascript) dates `legacy-javascript` 0.0.4 to 10/23, after the prior validation. Its [version metadata](https://registry.npmjs.org/legacy-javascript/0.0.4) and SHA512-verified package diff show changes to the version and two es-shims regular-expression lines; exported APIs, dependencies, engines, and the Apache-2.0 license stay unchanged. The [upstream fix and tests (#17421)](https://github.com/GoogleChrome/lighthouse/commit/0fbb25065f4f450706610b872edb1ab279504cc8) cover matching multiple polyfills and rejecting mismatched property names. Follow this normal owner resolution and retain the exact npm-tree and owner-graph guards; final-image runtime, scanner, and native release verification remain separate.

Wrangler owns its Miniflare/workerd selection and native Sharp graph. Keep its published Miniflare 5.20261019.1-beta, workerd 1.20261019.1, Sharp 0.35.5, libvips 1.3.4, and esbuild 0.28.2 versions together. Do not select a separate workerd or Miniflare build.

Debian packages resolve from the current official Trixie repositories during the build. Refreshing the apt layer does not promise byte-for-byte reproducibility. Ubuntu workflow jobs remain on 24.04.

## Security delivery policy

Trivy and Docker Scout keep their full Critical/High and secret reports. A third-party package finding can be accepted only when scanner output confirms the package, installed version, upstream vulnerability identity, and finding provenance. Record every accepted finding in the release evidence. Acceptance allows delivery under the approved policy; it does not mean the vulnerability is fixed, unreachable, or safe. Secret findings, HolyCode-owned findings, unknown package provenance, invalid or missing reports, and scanner execution failures block release.

The application dependency graph uses certifi 2026.10.19. pip 26.2.2 also bundles that version, replacing pip 26.2.1's affected certifi 2026.6.17 (`GHSA-6q48-6c7w-9gw2`). The official wheel comparison leaves the msgpack, `pkg_resources` and urllib3 repair subtrees unchanged. Reapply those existing repairs without adding a new vendor patch, rebase the BOM on the official 26.2.2 metadata, and retain msgpack 1.2.2, `pkg_resources` 78.1.1 and urllib3 2.8.0. The source wheel hash, installed RECORD, licenses, rebuilt offline seed and runtime consumers must pass together; a pip version bump alone does not qualify the change.

Scout SARIF rules can list multiple affected package versions shared by separate result rows. Match each result's reported package to its rule PURL instead of multiplying every result by every rule PURL. Preserve actual repeated observations and raw scanner evidence. Missing or ambiguous associations, unknown provenance and project-owned findings still block acceptance; the accepted JSON schema is unchanged. Report normalized result counts separately from unique vulnerability IDs.

The currently published v1.2.7 image uses Chromium `155.0.8059.39-1~deb13u1`. The selected v1.2.8 floor is official Debian Trixie `155.0.8059.79-1~deb13u1` for Chromium, common, and sandbox packages on AMD64 and ARM64. Package availability is not proof about a built or published HolyCode image. The previous ARM64 package exception is no longer used by the release workflow; the historical exception record remains unchanged. Do not custom-build or patch Chromium.

Open [issue #14](https://github.com/CoderLuii/HolyCode/issues/14) tracks the scanner findings on the currently published image. Keep it open until both final published platform images are scanned by Trivy and Docker Scout, the exact findings tracked by the issue are absent from the final scanner union, image digests and platform manifests are verified, and the recorded evidence is linked to that release. A higher package version by itself does not close the issue. Keep sandboxing, seccomp, the non-root user, and the closed browser port unchanged.

## Compatibility holds

| Component | Decision |
| --- | --- |
| Paperclip 2026.831.1 | Preserve service behavior, integrations, and user data. Newer releases need a controlled migration and untouched-data rollback exercise. |
| TypeScript 6.0.3 | Keep the stable programmatic API and `tsserver` feature. TypeScript 7 needs a separate compatibility migration. |
| json-server 0.17.4 | Keep the stable release instead of the 1.0 beta. |
| Apprise 1.13.1 | Defer the 2.0 major change until notifier and API compatibility is tested. |
| Claude Auth 2.2.1 (`opencode-claude-auth`) | Keep the current plugin because version 3 changes the OpenCode configuration contract. Issue #11 closed after the reporter switched plugins; the thread does not verify that Claude Auth's refresh problem is fixed, so this release makes no fix claim. |
| Existing PM2 owner replacements | Preserve js-yaml and basic-ftp consumer behavior. Remove each replacement only when the official owner graph contains a compatible fixed version and its consumer fixtures pass. |
| Existing pip vendor repairs | Select official pip 26.2.2 with its fixed Certifi bundle and preserve the same verified msgpack, `pkg_resources`, and urllib3 repairs, licenses, RECORD and offline seed. Keep the existing repair mechanism; do not add patches, forks, or custom builds. |
| `opencode-claude-auth` and provider configuration | Keep user-owned credentials, plugin settings, provider endpoints, and existing configuration untouched. |

Do not change Paperclip's data model, native-runner default, user data, provider settings, Claude Auth behavior, external CLIProxyAPI endpoints, or existing Hermes data as part of this dependency maintenance. The offline fixtures do not establish a live account, provider, OAuth, or billing result. HolyCode-managed Hermes and oh-my-openagent behavior remain as in v1.2.7. The local harness-agnostic feature branch and its unfinished workspace provisioning work are separate from this release.

The associated website is maintained in `CoderLuii/holycode-site`. Its Node/Astro/Vite update, copy synchronization, browser matrix, and deployment are a separate follow-up after the product release. The product release does not establish that the website has been updated or deployed.

## Local checks and hosted gates

Run these local equivalents before the direct-main commit:

- `python -m unittest discover -s tests`
- `python scripts/validate_workflow_pins.py`, `python scripts/validate_chromium_seccomp.py`, JSON/YAML and Compose validation, and the pinned Renovate extraction check
- Exact npm lifecycle policy and installed package owner-graph checks; Prisma, Paperclip, Wrangler, npm node-gyp, PM2, Python, Chromium sandbox, and plugin-mode fixtures
- AMD64 image build and full smoke, configuration, upgrade/rollback, scanner, and secret checks
- ARM64 emulation only when the local host can execute it; report emulation separately from native ARM64
- Headless local browser checks with isolated contexts, responsive viewport checks, saved screenshots, and no visible browser or report auto-open

The native AMD64 and ARM64 image smokes and plugin modes remain release gates. The hosted workflow jobs map to these local checks, but Windows/Linux package behavior and emulated ARM64 do not replace the native `ubuntu-24.04-arm` job. Native AMD64 and ARM64 runs remain required for the release. A local ARM64 emulated build was attempted and stopped at the first Dockerfile execution step with `/bin/sh: exec format error`; it produced no ARM64 image, smoke result, or scanner report. Do not change shared Docker or binfmt settings to retry. The documented native ARM host was unreachable during this audit. Use the manual pre-tag workflow only for its native AMD64/ARM64 validation and scanner evidence after local checks and the source push. A runner allocation, quota, billing, or Docker Hub service failure is an unavailable gate, not a code pass; do not retry billing-blocked Actions. Do not create a release tag or publish an image until the required native checks and scanner gates pass.

Once the local gates pass, use one direct-main commit titled `v1.2.8`, with `v1.2.7` as its sole release predecessor. Do not create a release PR or move a published tag. After the hosted protected release workflow succeeds, verify the GitHub release and assets, Docker Hub and GHCR `1.2.8`/`latest` index digests, both native platform manifests, SBOM, provenance, scanner reports, and upgrade/rollback evidence. Any failure before release or deployment must be entered in the repository's release failure ledger with the exact failed job/step, cause, and correction before the next attempt.
