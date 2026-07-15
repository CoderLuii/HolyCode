# HolyCode v1.1.2 Dependency Audit

**Audit date:** 07/15/2026

This record covers the Debian Trixie, Python 3.13, and npm 12 migration in `v1.1.2`. Registry versions, image manifests, release assets, checksums, licenses, and advisories were rechecked on the audit date. Every reviewed dependency ended as adopted, held, or removed.

## Adopted

| Component | Release decision | Evidence |
|-----------|------------------|----------|
| Node base | `node:24.18.0-trixie-slim@sha256:ae91dcc111a68c9d2d81ff2a17bda61be126426176fde6fe7d08ab13b7f50573` | Node 24 LTS on the immutable multi-architecture Trixie manifest |
| Debian / Python | Trixie 13.6 / Python 3.13.5 | Rebuilt package inventory, Python import checks, and `pip check` on AMD64 and ARM64 |
| npm | `12.0.1` | Exact lifecycle policy plus functional checks for every blocked installer |
| OpenCode | `1.18.2` | Exact CLI version and service smoke |
| NumPy | `2.5.1` | Python 3.13 import and full `pip check` |
| Wrangler | `4.111.0` | Modern service-environment dry run passes; removed `legacy_env` behavior fails as expected |
| lazygit | `0.63.1` | AMD64 SHA-256 `8e033bc78c8e192dee9510e951f6c9e154289b7198d22c924ed1d0a951b0dac1`; ARM64 SHA-256 `555dbc9a8efcf2e33bc24e7fbd9463e9fa375e3c5e23cc270763733c38eeae36` |
| Packaging | `26.0` | Hermes' exact pin installed in `/usr/local`; `pip check` passes |

## Held

| Component | Version | Reason |
|-----------|---------|--------|
| Node.js | `24.18.0` | Remains on the LTS line; Node 26 Current is outside this release train |
| Claude Code | `2.1.210` | Current audited stable pin |
| Paperclip | `2026.707.0` | Current audited stable pin; onboarding, Skills, persistence, and embedded PostgreSQL pass on both architectures |
| Hermes | `v2026.7.7.2@b7751df34688835a108e0d630f3495fc11f3df79` | Current audited release and commit |
| pnpm / tsx | `11.13.0` / `4.23.1` | Current audited pins from `v1.1.1` |
| TypeScript | `6.0.3` | TypeScript 7 is not a stable drop-in compiler or programmatic API for the bundled toolchains; no experimental alias is shipped |
| Vercel | `54.21.0` | Vercel 56.2.0 personal and team/scope behavior could not be proven without maintainer credentials |
| Netlify CLI | `26.2.0` | Installed without optional local-functions binaries; supported for remote build/deploy commands only |
| Requests / Pillow / Rich | `2.33.0` / `12.2.0` / `14.3.3` | Hermes requires these exact versions |
| json-server | `0.17.4` | The newer 1.0 release remains a beta |
| OpenCode plugins | `opencode-claude-auth@2.0.0`; `oh-my-openagent@4.18.1` | Exact startup defaults retained; manual mode preserves user choices and auto mode syncs to these pins |

## Removed

| Component | Decision |
|-----------|----------|
| Bundled CLIProxyAPI sidecar | Remains removed because its `v7.2.77` image contains fixable high-severity Go dependencies; external `CLIPROXYAPI_*` endpoints remain supported |
| Netlify local functions binaries | Remain removed; `netlify dev` and local functions are unsupported |

## npm Lifecycle Policy

npm 12 runs in deny-by-default mode. The image permits three lifecycle-script packages per architecture: OpenCode 1.18.2, Claude Code 2.1.210, and the matching `@embedded-postgres/linux-*` 18.1.0-beta.16 package. The embedded PostgreSQL script is required to create the packaged library symlinks before Paperclip drops to its unprivileged user.

The policy blocks 12 installed lifecycle-script packages per architecture, including esbuild, Prisma engines, Sharp, workerd, Netlify, Parcel watcher, ssh2, and cpu-features. Their supported binaries or code paths are exercised directly during the build and smoke tests. Any added package, version, script body, or architecture mismatch fails the image build.

Without the embedded PostgreSQL allow entry, Paperclip attempted to create links such as `libecpg.so.6` at runtime and failed with `EACCES`. The final image runs the exact hydration script at build time and verifies every link declared in `native/pg-symlinks.json`.

## Validation

- Built and smoked `linux/amd64` and `linux/arm64` images with Node 24.18.0, npm 12.0.1, Debian 13, Python 3.13.5, OpenCode 1.18.2, NumPy 2.5.1, Wrangler 4.111.0, and the held tool pins.
- Verified OpenCode, Paperclip onboarding and Skills, Hermes, Chromium, Claude Code, Netlify remote commands, npm plugin modes, UID/GID 2345 remapping, NAS-style bind mounts, writable paths, and restart persistence.
- Upgraded copied `v1.1.1` volumes to the `v1.1.2` candidate and rolled back with untouched pre-upgrade volumes on both architectures.
- Verified Wrangler's modern environment fixture and the expected failure for removed `legacy_env` configuration.
- Did not adopt Vercel 56.2.0 because authenticated personal and team/scope tests were unavailable. This is a documented hold, not a successful compatibility claim.
- Protected validation removes BuildKit's duplicate cache after loading the current image and before pulling `v1.1.1`, leaving both tagged images available for the upgrade and rollback test without exhausting GitHub-hosted runner storage.

## Security And Supply Chain

- Trivy 0.72.0 reported 30 critical and 269 high package occurrences per architecture. The critical entries collapse to 12 Debian CVE/package groups, all without a Trixie fixed version. No fixable critical finding and no secret were detected.
- Docker Scout 1.23.1 reported 19 vulnerable packages and 34 distinct high/critical vulnerabilities per architecture. Its critical-and-fixed gate found no vulnerable package.
- `CVE-2026-56367`, the fixable ImageMagick issue that blocked the Bookworm release gate, is absent. Trixie's newer `CVE-2026-56372` finding has no repository fix and remains visible in the scanner record.
- Trivy SPDX output contains 3,985 packages and 8,430 relationships for AMD64, and 3,980 packages and 8,410 relationships for ARM64.
- The base image uses an immutable manifest digest. s6-overlay, lazygit, Hermes, and other downloaded release assets use exact versions and checksums or commit verification. GitHub Actions use commit SHAs.
- Optional OpenCode plugins install at boot and remain outside the immutable image SBOM. Renovate covers images, Actions, npm, PyPI, GitHub releases, and plugin pins, but maintainer review remains required.

No vulnerability exception is used for `v1.1.2`. The audit does not claim universal freshness, byte-for-byte rebuilds, or zero vulnerabilities.

## Translation Change Map

The English source changed in these translated sections:

1. Runtime table: npm 12.0.1 and Python 3.13 on Trixie.
2. Release summary: OpenCode 1.18.2, Wrangler 4.111.0, lazygit 0.63.1, and NumPy 2.5.1 are adopted.
3. Holds and removals: TypeScript 6.0.3, Vercel 54.21.0, Netlify remote-only support, and the removed bundled CLIProxyAPI sidecar remain explicit.

All ten translated READMEs were checked against this map.
