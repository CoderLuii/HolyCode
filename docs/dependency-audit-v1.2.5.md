# HolyCode v1.2.5 Dependency Audit

Date: 10/05/2026

The release predecessor is `v1.2.4`. Upgrade and rollback checks use `coderluii/holycode:1.2.4@sha256:26dc14d6823573a0aa2b12469c93cbbf6492c1498bbb588a7a0b0c88c42c4a23`, the published Docker Hub and GHCR index.

This records the selected source graph. It does not establish publication or native runtime verification. The release assets and final workflow record the exact shipped images, native checks, SBOMs, provenance, scanner reports, and registry aliases.

## Selected official updates

| Component | v1.2.4 | v1.2.5 source selection | Verification boundary |
| --- | --- | --- | --- |
| [Claude Code](https://registry.npmjs.org/%40anthropic-ai%2Fclaude-code/2.1.290) | 2.1.286 | 2.1.290 | Exact package integrity, native payload, notices, non-root startup |
| [OpenSpec (`@fission-ai/openspec`)](https://registry.npmjs.org/%40fission-ai%2Fopenspec/1.14.1) | 1.14.0 | 1.14.1 | Explicit project initialization; telemetry remains disabled |
| [pnpm](https://registry.npmjs.org/pnpm/12.9.1) | 12.8.1 | 12.9.1 | Exact lifecycle script and package integrity |
| [ESLint](https://registry.npmjs.org/eslint/10.12.0) | 10.11.0 | 10.12.0 | Installed CLI smoke |
| [Wrangler](https://registry.npmjs.org/wrangler/4.147.0) | 4.145.0 | 4.147.0 | Matching Miniflare 5.20261001.0-alpha and workerd 1.20261001.1; runtime smoke |
| [lazygit](https://github.com/jesseduffield/lazygit/releases/tag/v0.66.0) | 0.65.1 custom source build | 0.66.0 official release binaries | Exact AMD64/ARM64 release checksums; CLI/version checks |
| [GitHub CLI](https://github.com/cli/cli/releases/tag/v2.102.0) | 2.102.0 custom source build | 2.102.0 official release archives | Exact AMD64/ARM64 checksums; unchanged CLI commands |
| [fzf](https://github.com/junegunn/fzf/releases/tag/v0.74.4) | 0.74.4 custom source build | 0.74.4 official release archives | Exact AMD64/ARM64 checksums; unchanged CLI commands |
| [delta](https://github.com/dandavison/delta/releases/tag/0.20.1) | 0.19.2 | 0.20.1 official release binaries | Exact AMD64/ARM64 checksums; Git pager smoke |
| Paperclip range-resolved packages | Cursor SDK 1.0.35, jsdom 30.1.1 | Cursor SDK 1.0.36, jsdom 30.1.2 | Declared upstream ranges; existing owner and jsdom fetch checks; Undici 8.11.2 unchanged |
| Debian Chromium | ARM64 .57 under temporary exceptions | At least 154.0.8037.92-1~deb13u1 on both platforms | Fresh package resolution, installed package inventory, browser sandbox smoke |

Node 24.21.0 and its Trixie-slim index remain unchanged. The custom GitHub CLI, fzf, and lazygit build stages are removed; no custom Go builder is needed. The October 5 apt refresh prevents a cached October 1 package install. It does not make distro resolution byte-for-byte reproducible.

## Security delivery policy

Trivy and Docker Scout continue to produce their full Critical/High reports. A third-party finding must identify its ecosystem, package, installed version, and vulnerability ID consistently before it can be recorded as an accepted upstream vulnerability. The accepted-finding JSON records accompany the native scanner evidence. Acceptance permits delivery; it does not mean the vulnerability is fixed, unreachable, or safe.

Secret findings, HolyCode-owned package findings, missing or unrecognized package provenance, malformed or missing reports, and scanner execution failures still block release. npm lifecycle checks, browser sandbox/seccomp checks, runtime tests, and release commit/digest checks remain active.

The active v1.2.4 ARM64 Chromium exception is removed. The published v1.2.4 tag remains unchanged and its ARM64 image still contains the affected .57 packages. [Debian DSA-6535-1](https://lists.debian.org/debian-security-announce/2026/msg00448.html) identifies .92 as the corrected version. A fix claim requires the installed packages and fresh native evidence; changing a source minimum alone is insufficient.

Native pre-tag inventories confirm `154.0.8037.92-1~deb13u1` for all three Chromium packages on AMD64 and ARM64. Docker Scout still reports five newer vulnerabilities against `chromium-sandbox` at that version: [CVE-2026-103622](https://security-tracker.debian.org/tracker/CVE-2026-103622), [CVE-2026-103624](https://security-tracker.debian.org/tracker/CVE-2026-103624), [CVE-2026-103625](https://security-tracker.debian.org/tracker/CVE-2026-103625), [CVE-2026-103626](https://security-tracker.debian.org/tracker/CVE-2026-103626), and [CVE-2026-103628](https://security-tracker.debian.org/tracker/CVE-2026-103628). Debian marks .92 vulnerable; [Google identifies .97 as the upstream Linux fix](https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop.html), but Debian has not published that package. These are accepted upstream vulnerabilities on both platforms, including two Critical findings. They are separate from the old .57 exception and are not fixed by this release. Avoid untrusted browser content and automation until the corrected Debian packages ship. The existing sandbox, seccomp profile, unprivileged user, and closed browser port reduce exposure; they do not make these flaws safe or unreachable. Rebuild from an official Debian package once .97 or newer becomes available, then verify the installed versions and rerun both scanners.

## Compatibility holds and deferred replacements

| Component | Decision and reason |
| --- | --- |
| Paperclip 2026.831.1 | Keep current product features and settings. 2026.1001.0 has a supported native-runner control, but removes legacy Composio connections without a verified migration. Do not combine that data migration with this maintenance release. |
| TypeScript 6.0.3 | Keep the stable programmatic API and `tsserver` feature. TypeScript 7 needs a separate integration migration. |
| Prisma 7.10.0 / json-server 0.17.4 | Keep stable releases; do not switch to Prisma 8 RC or json-server 1 beta. |
| Python inputs and locks | Keep the released pip-tools 7.6.1 boundary. Its required header correction is merged upstream but not yet in a released pip-tools version. Do not add a manual workaround or extend pip vendor repairs. |
| Existing npm/PM2 owner replacements | Preserve the existing graph. Defer the nested ip-address, node-gyp, and basic-ftp replacements because refreshing them through the current package-tree repair would extend manual third-party modifications. Await official owner releases or a verified normal-resolution integration. |
| Wrangler-owned Sharp/libvips replacements | Preserve the existing integration; do not extend its third-party package replacement just to chase newer nested pins. |
| Claude Auth 2.2.1 | Keep the official offline payload. Upstream has no demonstrated fix for proactive credential refresh. [Issue #11](https://github.com/CoderLuii/HolyCode/issues/11) stays open until failing-before/passing-after evidence or reporter-confirmed recovery. |
| External CLIProxyAPI integration | Preserve endpoint support and explicit model settings. A separate plugin/API-key path does not establish a Claude Auth fix. |

Existing Hermes data and user-managed plugin settings remain preserved. Hermes service and HolyCode-managed oh-my-openagent installation remain suspended as documented; this release does not silently re-enable them.

## Required release checks

Before tagging, use one validated direct-main commit titled `v1.2.5`, with `v1.2.4` as its sole release predecessor. Require source tests, workflow pins, Compose and seccomp checks, lifecycle and package inventories, native AMD64 and ARM64 image smokes and plugin modes, rollback checks, both scanner reports and accepted-finding records, SBOM and provenance.

The image smoke must cover Claude startup without live credentials and the marketplace path-containment regression. That test does not establish a live account, provider, OAuth, or billing result.

After publication, verify GitHub release assets, Docker Hub and GHCR `1.2.5`/`latest` digests, both platform manifests and attestations, and the product website's published-release sync. An unavailable runner is a blocker, not a passing check. Do not create a release PR or mutate existing version tags.
