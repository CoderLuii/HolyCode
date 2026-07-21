# HolyCode v1.1.3 Dependency Audit

**Audit date:** 07/21/2026

This record covers the security and compatible dependency refresh in `v1.1.3`. Registry versions, image manifests, release assets, checksums, licenses, and advisories were rechecked on the audit date. Every reviewed dependency ended as adopted, held, or removed.

## Adopted

| Component | Version | Validation |
|-----------|---------|------------|
| OpenCode | `1.18.4` | Exact CLI version, web service smoke, and plugin-mode tests |
| Claude Code | `2.1.216` | Exact CLI version plus authentication-volume persistence gate |
| s6-overlay | `3.2.3.2` | Official AMD64, ARM64, and noarch release assets with SHA-256 verification |
| fzf | `0.74.1` | Official AMD64 and ARM64 release assets with SHA-256 verification |
| pnpm | `11.15.1` | Exact CLI version and install smoke |
| Vite / Prettier | `8.1.5` / `3.9.6` | Exact CLI versions |
| Wrangler | `4.112.0` | Exact CLI version with its matching blocked Workerd lifecycle entry |
| Prisma | `7.9.0` | Exact CLI and engines versions with lifecycle policy checks |
| Lighthouse | `13.4.1` | Exact CLI version; LHCI is not installed |
| OpenCode plugins | `opencode-claude-auth@2.0.0`; `oh-my-openagent@4.19.0` | Fresh, manual, automatic, and disabled startup modes |
| Renovate validator | `43.274.0` | Exact CI version and strict config validation |
| Python security refresh | pip `26.1.2`; Requests `2.34.2`; Pillow `12.3.0`; wheel `0.47.0` | Python imports, exact version checks, and `pip check` |
| Python compatible refresh | matplotlib `3.11.1`; tqdm `4.69.0`; FastAPI `0.139.2`; Packaging `26.2`; Rich `15.0.0` | Python imports, exact version checks, and `pip check` |
| GitHub CLI | `2.96.0` at `b300f2ec7ec9dc9addc39b2ad88c54097ded7ca0` | Exact upstream tag rebuilt with digest-pinned Go `1.26.5`; source commit, embedded toolchain, and CLI version checks |

## Held

| Component | Version | Reason |
|-----------|---------|--------|
| Node base | `node:24.18.0-trixie-slim@sha256:ae91dcc111a68c9d2d81ff2a17bda61be126426176fde6fe7d08ab13b7f50573` | Remains on the digest-pinned LTS base and rebuilds against current Trixie repositories |
| npm | `12.0.1` | Current image pin; covered by the lifecycle policy |
| Paperclip | `2026.707.0` | `2026.720.0` contains a destructive automatic migration chain that requires separate persistence testing |
| Netlify CLI | `26.2.0` | Remote build/deploy commands only; optional local-functions binaries remain absent |
| TypeScript | `6.0.3` | TypeScript 7 is not a compatible default programmatic API for every bundled toolchain |
| json-server | `0.17.4` | The 1.0 release remains a beta |

Paperclip's published Connect 1.x dependency still declares Undici 5 and installs vulnerable Undici 5.29.0. HolyCode replaces that nested package with Undici 6.27.0 and updates Connect's installed dependency declaration to match. The image build and smoke test require a valid `npm ls undici --all` tree and exercise the Cursor adapter's environment check. Remove this reviewed compatibility patch when Paperclip updates Connect upstream.

## Removed

| Component | Decision |
|-----------|----------|
| Hermes Agent | Bundled runtime and service removed while current releases pin vulnerable Pillow and add unresolved cryptography, MCP, and Starlette findings; `/home/opencode/.hermes` remains untouched |
| Vercel CLI | Removed because its current dependency tree still contains a fixable critical finding |
| sharp-cli | Removed because its current dependency tree contains fixable high findings |
| concurrently | Removed because its current dependency tree contains vulnerable `shell-quote` |
| LHCI | Removed because its current dependency tree contains vulnerable `tmp`; regular Lighthouse remains installed |
| Bundled CLIProxyAPI | Remains external-only until published binaries have verifiable compiler provenance and pass `govulncheck`; `CLIPROXYAPI_*` provider configuration remains supported |

Hermes restoration is tracked against [PR #63942](https://github.com/NousResearch/hermes-agent/pull/63942), [issue #60841](https://github.com/NousResearch/hermes-agent/issues/60841), and [issue #60685](https://github.com/NousResearch/hermes-agent/issues/60685).

## npm Lifecycle Policy

All global npm packages are installed with lifecycle scripts disabled. The build then validates each script-bearing package's exact version, npm integrity, architecture rule, and script body against `config/npm-global-script-policy.json`.

Only OpenCode 1.18.4, Claude Code 2.1.216, and the active architecture's Paperclip embedded PostgreSQL package may run reviewed scripts. Installed but unneeded scripts remain blocked, including esbuild, Prisma engines, Sharp, Workerd, Netlify, ssh2, and cpu-features. A new package, changed version, changed integrity, changed script body, or unmatched architecture stops the image build.

## Chromium Sandbox

Chromium runs as `opencode` with the Debian sandbox helper installed. Docker Compose applies `config/chromium-seccomp.json`, the constrained namespace profile vendored from Playwright. The release gate launches system Chromium through Playwright and requires a nonblank screenshot on AMD64 and ARM64. `--no-sandbox`, `SYS_ADMIN`, and `seccomp=unconfined` are not accepted fallbacks.

## Image Evidence

Protected validation builds one attested AMD64/ARM64 candidate from the exact release commit and records its immutable digest, Debian inventories, SBOMs, and scanner reports as workflow artifacts. Native architecture jobs pull that exact digest for smoke, upgrade, rollback, Chromium, Docker Scout, and Trivy gates. Publication promotes the same validated digest to Docker Hub and GHCR instead of rebuilding it. The release workflow verifies that `1.1.3` and `latest` resolve to the candidate digest with both platforms and provenance attestations.

The candidate digest and final package counts are intentionally recorded in protected workflow evidence and the release summary. They cannot be known before the release commit is finalized, and Debian packages resolve from current Trixie repositories during that candidate build.

## Upgrade And Rollback

The release gate upgrades copied `v1.1.2` volumes to the candidate image. It verifies OpenCode state, Paperclip state, persisted Claude credential files, plugin behavior, writable paths, and an untouched `.hermes` marker. A maintainer separately verified the real Claude authentication flow without exposing credentials to CI. Bundled Hermes is not started in v1.1.3.

Rollback means stopping the candidate, restoring untouched pre-upgrade volumes, and starting image `1.1.2`. An in-place Paperclip or other database downgrade is not supported.

## Residual Findings

The pre-release Docker Scout database reported the following unfixable critical/high findings on both architectures on 07/21/2026. Protected validation records the final count against the exact candidate digest:

| Package and layer | Findings | Reachability and upstream status |
|-------------------|----------|----------------------------------|
| Debian `perl` 5.40.1-6 | `CVE-2026-12087`, `CVE-2026-48959`, `CVE-2026-48962` | No bundled service calls the affected Socket or IO::Compress APIs with untrusted input. They remain reachable to an interactive shell user. Debian Trixie has no fixed package; Debian marks the module updates as minor/no-DSA work and unstable carries partial fixes. Review after the next Trixie security update. |
| Debian `vim` 2:9.1.1230-2 | `CVE-2026-34982`, `CVE-2026-52860`, `CVE-2026-52858`, `CVE-2026-47162` | Interactive only. Exploitation requires opening crafted content and using modelines, Python omni-completion, or netrw. No HolyCode service invokes Vim. Upstream fixes exist, but Debian Trixie has no fixed package. Do not open untrusted files in Vim until Trixie publishes the update. |
| Debian `libheif` 1.19.8-1 | `CVE-2026-32740`, `CVE-2026-32882`, `CVE-2026-32741` | ImageMagick is the installed consumer, and its system policy denies every coder except GIF, JPEG, PNG, and WEBP. The smoke test enforces that policy, so HEIF/AVIF decoding is blocked. Debian Trixie has no fixed package; sid carries 1.23.1. |
| Debian `libde265` 1.0.15-1 | `CVE-2026-33164` | Pulled by `libheif`; the same ImageMagick policy blocks its HEIF/H.265 path. Debian Trixie has no fixed package; newer Debian suites carry a fix. |
| `github.com/docker/cli` in `/usr/local/bin/gh` | `CVE-2025-15558` | The advisory affects Windows Docker CLI plugin lookup. HolyCode runs the GitHub CLI inside Linux and does not expose Docker CLI plugin discovery, so this path is not reachable. Scout does not recognize the OS-specific condition in the embedded Go module. |

The first local candidate exposed `CVE-2026-39822` in the Go 1.26.4 standard library embedded in GitHub CLI 2.96.0. GitHub had not published a newer CLI release, so the final candidate rebuilds that exact upstream tag with Go 1.26.5, which contains the standard-library fix. The release is blocked unless both Docker Scout and Trivy report zero **fixable** critical and zero **fixable** high findings. This audit does not claim universal freshness, byte-for-byte rebuilds, zero total findings, or that future rebuilds will retain the same scanner result.

## Translation Change Map

The English source changed in these translated sections:

1. Runtime and release pins: OpenCode 1.18.4, Claude Code 2.1.216, updated compatible tools, and plugin 4.19.0.
2. Holds and removals: Paperclip 2026.707.0 retained; bundled Hermes and vulnerable global CLIs removed.
3. Browser guidance: Chromium uses the shipped constrained seccomp profile with its sandbox enabled.
4. Migration behavior: old `ENABLE_HERMES=true` deployments stop with a clear message while `.hermes` data remains untouched.

All ten translated READMEs are checked against this map before release.
