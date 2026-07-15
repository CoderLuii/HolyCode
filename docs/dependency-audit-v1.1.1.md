# HolyCode v1.1.1 Dependency Audit

Audit date: 07/15/2026

This record covers the Bookworm security refresh shipped in `v1.1.1`. Registry versions, image manifests, release assets, checksums, licenses, and security advisories were rechecked on the audit date. A newer version was not adopted unless the HolyCode runtime gates supported it.

## Adopted

| Component | Version | Evidence and disposition |
|-----------|---------|--------------------------|
| Node base | `node:24.18.0-bookworm-slim@sha256:6f7b03f7c2c8e2e784dcf9295400527b9b1270fd37b7e9a7285cf83b6951452d` | Latest Node 24 LTS Bookworm manifest on the audit date |
| OpenCode | `1.18.1` | Current stable npm release |
| Claude Code | `2.1.210` | Current stable npm release |
| s6-overlay | `3.2.3.1` | Current GitHub release; noarch and architecture archives are SHA-256 verified |
| pnpm | `11.13.0` | Current stable npm release; install and command smoke tests required |
| tsx | `4.23.1` | Current stable npm release |
| `oh-my-openagent` | `4.18.1` | Current stable npm release and default plugin pin |
| ImageMagick | `8:6.9.11.60+dfsg-1.6+deb12u12` | Current Bookworm security package; includes the Debian fix for `CVE-2026-56367` |

## Held

| Component | Version | Reason |
|-----------|---------|--------|
| Node | `24.18.0` | Node 24 is LTS; Node 26 remains the Current line |
| npm | `11.16.0` | npm 12 lifecycle-script policy is evaluated with the Trixie migration in `v1.1.2` |
| Paperclip | `2026.707.0` | Current stable npm release |
| Hermes | `v2026.7.7.2` at `b7751df34688835a108e0d630f3495fc11f3df79` | Current release; tag-to-commit check remains enforced |
| TypeScript | `6.0.3` | TypeScript 7 does not yet expose the stable programmatic API required by the bundled toolchains |
| Wrangler | `4.110.0` | `4.111.0` migration behavior is evaluated in `v1.1.2` |
| Vercel | `54.21.0` | `56.2.0` requires authenticated personal and team/scope validation |
| Netlify CLI | `26.2.0` | Current release; remote build/deploy only after removing local functions binaries |
| NumPy | `2.4.6` | Bookworm Python 3.11 cannot install NumPy 2.5.1, which requires Python 3.12 or newer |
| Requests | `2.33.0` | Hermes v2026.7.7.2 exact-pins this CVE-fixed release |
| Pillow | `12.2.0` | Hermes v2026.7.7.2 exact-pins this release for its vision recovery path |
| Rich | `14.3.3` | Hermes v2026.7.7.2 exact-pins this release |
| json-server | `0.17.4` | Latest stable release; registry `latest` is a 1.0 beta |
| `opencode-claude-auth` | `2.0.0` | Current stable npm release |

## Removed

| Component | Reason | Restoration trigger |
|-----------|--------|---------------------|
| Bundled CLIProxyAPI sidecar | Trivy 0.72.0 reports 14 fixable high-severity findings in `eceasy/cli-proxy-api:v7.2.77`, including affected `x/crypto`, `x/net`, and `go-billy` modules | Restore only after upstream publishes a rebuilt multi-architecture image and the same protected gates pass |
| Netlify `local-functions-proxy-*` binaries | npm installs platform binary 1.1.1 even with `--omit=optional`; the binary remains security-flagged | Restore `netlify dev` and local functions only after upstream rebuilds the binaries and the image scan passes |
| `.trivyignore.yaml` exceptions | The vulnerable Netlify binaries are no longer in the image, so their exceptions are unnecessary | Reintroduce only through the documented time-limited exception policy |

External CLIProxyAPI endpoints remain supported through `CLIPROXYAPI_ENABLED`, `CLIPROXYAPI_BASE_URL`, `CLIPROXYAPI_API_KEY`, and model settings. HolyCode does not bundle, start, or update that external service.

## Supply Chain

- The Node base is pinned by multi-architecture manifest digest.
- s6-overlay 3.2.3.1 uses release-provided SHA-256 values: `43d99d266fefe32cdc1510963aaadeb211cc8450b60af27817b64af450c934be` for noarch, `ed72fdb3abf196472d121b026bed63b46f3443507bd2ce67df6bd187f7d4dc0a` for x86_64, and `c79b5cc7e5e405f6e1ae1466a8160ac84d29b86614e1e01ff0fb11dc832fee1b` for aarch64.
- GitHub Actions remain pinned to full commit SHAs and are checked by `scripts/validate_workflow_pins.py`.
- Renovate 43.263.9 keeps dependency dashboard approval for runtime, service, major, Python, and prerelease updates. Pull requests validate the config before any extraction claim is made.
- Boot-installed OpenCode plugins remain outside the immutable image SBOM. `manual` preserves user versions; `auto` synchronizes the declared image pins.

## Security Disposition

- Upstream CLIProxyAPI report: [router-for-me/CLIProxyAPI#4341](https://github.com/router-for-me/CLIProxyAPI/issues/4341)
- Upstream Netlify report: [netlify/cli#8342](https://github.com/netlify/cli/issues/8342)
- Fixable critical findings block the release. `v1.1.1` carries no critical exception file.
- Trivy 0.72.0 recorded 34 critical package occurrences across 14 CVEs and no secrets on each architecture. Every critical entry had an empty fixed-version field, so the fixable-critical count was zero. The amd64 candidate had 386 high occurrences across 242 CVEs; arm64 had 385 across 241 CVEs. `CVE-2026-56367` was absent after installing ImageMagick `deb12u12`.
- Local Docker Scout recorded 58 critical/high vulnerabilities across 26 packages on each architecture. It indexed 3,050 amd64 packages and 3,044 arm64 packages, generating 9,072,559-byte and 9,058,873-byte SPDX documents respectively. Protected validation repeats Scout with the pinned 1.23.1 CLI for each architecture.
- Protected validation generates a per-architecture SPDX SBOM, Docker Scout SARIF report, Trivy critical/high report, provenance, and secret scan.

## Release Gates

The release must pass both `linux/amd64` and `linux/arm64` builds, image-version checks, Netlify binary-absence checks, Paperclip Skills loading, Hermes and OpenCode service smokes, plugin pin modes, UID/GID remapping, restart persistence, upgrade from `1.1.0`, and rollback with untouched `1.1.0` volumes.

The audit does not claim universal freshness, byte-for-byte rebuilds, or zero vulnerabilities. Debian packages resolve from the current Bookworm repositories during the release build, and residual scanner results remain visible in the protected workflow.
