# v1.3.1 dependency and release audit

This release refreshes compatible official tools and libraries and adopts the simplified GitHub release workflow. It keeps the existing services, persistent paths, provider setup, browser controls and compatibility holds. No third-party source, manifest or vendored distribution is patched.

## Release identity and delivery

The predecessor is `v1.3.0`, verified on Docker Hub and GHCR as `coderluii/holycode:1.3.0@sha256:0e720fccf15fe4a9c122d8c1b589812a11437e82376be4620341814d15f75b6f`. Release commit, tag and title match `v1.3.1`. Keep direct-main maintainer delivery and immutable version aliases/assets.

Run local source/static/consumer checks before committing or pushing. Then use one manual GitHub Actions release workflow: native AMD64 and native ARM64 builds, exact attested composition, read-only protected validation and guarded promotion. Do not run a duplicate pre-tag build or invent a new local controller. The [current release guide](local-validation.md) supersedes historical local-first release instructions. A validation-only run does not publish a product release.

The workflow promotes the qualified graph without rebuilding. Image identity, native results, inventories, full reports, accepted findings, SBOM/provenance and checksums belong to this exact release's assets. Previous-release or warm-cache results do not qualify changed images. Image signing is not configured; do not claim signatures.

## Compatible official updates

| Group | Selection |
| --- | --- |
| Base/runtime | Official Node 24.22.3 Trixie slim index, pinned by digest; Debian packages refreshed for this release |
| CLIs | Claude Code 2.1.325, GitHub CLI 2.104.0, fzf 0.75.0, lazygit 0.66.3 |
| JavaScript tools | pnpm 12.21.0, Vite 8.3.8, Prettier 3.10.1, ESLint 10.15.0, dotenv-cli 11.1.0 |
| Prisma owner graph | Prisma 7.10.1 retained with its exact published mysql2 3.24.4 dependency |
| Wrangler owner graph | Wrangler 4.162.0, declared Miniflare 5.20261113.0-beta and workerd 1.20261113.1; existing sharp/libvips expectations retained |
| Paperclip owner graph | Paperclip 2026.831.1 retained with official Cursor SDK 1.4.0, jsdom 30.1.3 and Undici 8.12.4 |
| Python 3.13 | Playwright 1.65.2, pandas 3.1.1, NumPy 2.5.5, Click 8.5.1, Markdown 3.11.3, FastAPI 0.163.1; compatible transitive dependencies recorded in hash locks |
| Delivery tools | Immutable Docker login action 4.8.0 and Trivy 0.76.2 archives/checksums |

Official npm/PyPI metadata, parent dependency declarations and release checksums were refreshed before selection. The Dockerfile's direct pins, lifecycle-script policy, checksums, exact owner guards and consumer tests move together. Python lock generation targets Linux Python 3.13 and preserves exact published hashes. The newer lock-generation tool is separate from the product's official pip distribution.

Upstream sources: [Node image](https://hub.docker.com/_/node), [Claude Code](https://www.npmjs.com/package/@anthropic-ai/claude-code), [Wrangler](https://www.npmjs.com/package/wrangler), [Paperclip](https://www.npmjs.com/package/paperclipai), [Prisma](https://www.npmjs.com/package/prisma), [Python package index](https://pypi.org/), [GitHub CLI](https://github.com/cli/cli/releases), [fzf](https://github.com/junegunn/fzf/releases), [lazygit](https://github.com/jesseduffield/lazygit/releases), [Trivy](https://github.com/aquasecurity/trivy/releases), [Docker login action](https://github.com/docker/login-action/releases).

## Compatibility holds and unchanged features

Paperclip 2026.831.1, Claude Auth 2.2.1, TypeScript 6.0.3, Prisma 7.10.1, json-server 0.17.4 and Apprise 1.13.1 remain selected. Major/beta migrations need separate contract, runtime, data and rollback evidence. Claude Auth 3 targets the newer OpenCode plugin contract; TypeScript 7 changes packaging and tsserver availability; Prisma 8 was prerelease; jsdom 31 is outside Paperclip's published owner range. OpenSpec stays on 1.14.3; its new 2.0 major migration is separate. Do not remove an existing feature to accept a newer version.

pnpm 12.21.0 keeps its official internal Undici 7.30.2 bundle. The package version, published integrity, embedded manifest hash and exact runtime expectation are bound by a regression fixture; no standalone Undici replacement is installed.

Official npm 12.2.2, PM2 7.1.2 and pip 26.3 retain their published graphs. Do not replace their owned node-gyp, Undici, js-yaml or pip vendor files using independent latest versions. Wrangler's declared Miniflare graph governs selection even when an independent dist-tag looks older. No routine update is accepted through a custom dependency patch.

Hermes and HolyCode-managed oh-my-openagent remain unavailable; preserve their data, settings, skills and caches. CLIProxyAPI remains external-only. Keep credentials and all home/cache/workspace mounts unchanged. The unrelated Codex/Gemini/ttyd feature branch and separate HolyCode Cloud service are outside this release.

## Security delivery policy

Preserve the non-root user, setuid Chromium sandbox, supplied seccomp profile and closed browser port. Official Debian Chromium/common/sandbox must meet the existing `156.0.8078.79-1~deb13u1` floor and current repository availability on both native platforms. Avoid untrusted browser content and automation while known upstream findings remain.

Retain full and fixable Trivy/Scout reports, secret checks, inventories and accepted-upstream records. Valid third-party vulnerability findings remain advisory under the established policy; acceptance does not fix them or establish safety. Project-owned findings, secrets, scanner/tool execution errors, malformed or missing reports and ambiguous artifact identity remain blocking. This is not a zero-vulnerability claim.

The source suite, strict workflow lint/config checks and real consumer checks precede push. Both native protected jobs must pass tool/browser sandbox, plugin, Hermes refusal/preservation, Chromium, upgrade/persistence/untouched-snapshot rollback, scanner and aggregate gates before promotion. Read actual image-bound release evidence rather than treating an available upstream version or cache hit as proof.

## Recovery and website follow-up

Roll back to the verified `v1.3.0` image with untouched pre-upgrade copies of home, local-cache and workspace. Never reuse volumes already opened by the newer image for a rollback test. Paperclip is unchanged, so this release introduces no Paperclip migration or native-runner default override.

Record the first actionable failure and exact input identity before retrying. Do not rerun deterministic failures unchanged. Reconcile partial promotion/uploads without deleting or overwriting public aliases/assets. Site or description failures must not restart qualified product builds.

After product publication, synchronize the separate site's real release facts and committed history, qualify its current UI headlessly, seal one build, deploy those exact bytes and verify immutable plus canonical URLs. Product publication alone does not prove website delivery.
