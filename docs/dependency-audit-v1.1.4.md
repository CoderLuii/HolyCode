# HolyCode v1.1.4 Dependency Audit

**Audit date:** 07/30/2026

This record covers the accessible security and dependency refresh in `v1.1.4`. Versions were resolved from Debian Trixie stable/security, official npm and PyPI registries, official GitHub releases, and official container images. An announced version without a compatible artifact was not treated as installable.

## Adopted

| Component | Version | Validation |
|-----------|---------|------------|
| OpenCode | `1.18.9` | Exact CLI version, service smoke, and plugin-mode checks |
| Claude Code | `2.1.220` | Exact CLI version, no-secret auth-status check, and credential-file persistence through the copied-volume upgrade |
| Paperclip | `2026.722.0` | Embedded PostgreSQL hydration, migrations `0136` through `0183`, onboarding, Skills, state persistence, and copied-volume upgrade |
| Paperclip Undici | `6.28.0` | Registry-integrity check, valid installed npm tree, and Cursor adapter environment check |
| npm | `12.0.2` | Exact CLI version with reviewed nested `brace-expansion@5.0.8` and `tar@7.5.22` replacements |
| pnpm / ESLint | `11.18.0` / `10.8.0` | Exact CLI versions |
| Wrangler / Prisma | `4.115.0` / `7.9.1` | Exact CLI versions with matching blocked Workerd and Prisma lifecycle entries |
| Claude Auth plugin | `opencode-claude-auth@2.1.5` | npm integrity verified at build time; packaged in the image and installed offline at startup |
| Python refresh | pandas `3.0.5`; tqdm `4.70.0`; FastAPI `0.141.1`; Uvicorn `0.52.0` | Hash-locked installation, imports, API/server smoke, and `pip check` |
| Python packaging seed | pip `26.2`; setuptools `83.0.0`; Packaging `26.2`; wheel `0.47.0` | Separate hash-locked offline seed and fresh virtual-environment bootstrap |
| pip vendored packages | msgpack `1.2.1`; pkg_resources from setuptools `80.9.0` | Exact PyPI source hashes, reviewed import patch, legacy metadata-backend smoke, BOM assertions, and scanner checks |
| GitHub CLI | `2.96.0` at `b300f2ec7ec9dc9addc39b2ad88c54097ded7ca0` | Exact source tag rebuilt with Go `1.26.5`, gRPC `1.82.1`, compress `1.18.7`, and x/text `0.39.0` |
| fzf | `0.74.1` at `eae8d9d27eaeffc777699c01bf8f8b8c071908c1` | Exact source tag rebuilt with x/sys `0.44.0` |
| lazygit | `0.63.1` at `aafe61082e7ed383d318fd40e48f85645e6afc7b` | Exact source tag rebuilt with x/text `0.39.0` |
| Renovate validator | `44.2.3` | Strict configuration plus local extraction of both pip-compile inputs and hash-locked outputs |
| Docker login Action | `v4.6.0` at `dbcb813823bdd20940b903addbd779551569679f` | Full commit pin checked by workflow validation |
| Node setup Action | `v7.0.0` at `820762786026740c76f36085b0efc47a31fe5020` | Full commit pin and Node 24.18.0 validation runtime |

## Held

| Component | Version | Reason |
|-----------|---------|--------|
| Node base | `node:24.18.0-trixie-slim@sha256:ae91dcc111a68c9d2d81ff2a17bda61be126426176fde6fe7d08ab13b7f50573` | Node 24.18.1 was announced on 07/28/2026, but the matching official multi-architecture Trixie image tag was not published at freeze time |
| TypeScript | `6.0.3` | TypeScript 7 is not a compatible default programmatic API for every bundled toolchain |
| json-server | `0.17.4` | The 1.0 release remains a beta |
| Paperclip Undici line | `6.28.0` | The current Paperclip/Connect package tree is compatible with Undici 6; jumping to a different major would be an unsupported substitution |

The remaining current pins were rechecked on 07/30/2026. s6-overlay `3.2.3.2`, fzf `0.74.1`, lazygit `0.63.1`, delta `0.19.2`, eza `0.23.5`, tsx `4.23.1`, Vite `8.1.5`, esbuild `0.28.1`, Prettier `3.9.6`, and Lighthouse `13.4.1` were already the newest compatible stable artifacts consumed by the image.

## Removed Or Suspended

| Component | Decision |
|-----------|----------|
| Netlify CLI | Removed from the image |
| `serve` | Removed from the image |
| oh-my-openagent | HolyCode-managed download and installation suspended while the current package tree retains unresolved security findings; the old active entry is disabled once while settings, skills, and cached package data remain |
| Hermes Agent | Remains unbundled while current releases require vulnerable dependency pins; `/home/opencode/.hermes` remains untouched |
| Vercel CLI, sharp-cli, concurrently, LHCI | Remain removed because their current dependency trees contain fixable critical or high findings |
| Bundled CLIProxyAPI | Remains external-only until published binaries have verifiable compiler provenance and pass `govulncheck`; `CLIPROXYAPI_*` provider configuration remains supported |

When `ENABLE_OH_MY_OPENAGENT=true` or `ENABLE_HERMES=true` remains in an older deployment, `v1.1.4` stops with a direct migration message. The oh-my-openagent stop happens before its state changes. After that flag is removed, the first successful start removes the legacy active entry from `opencode.json` and `tui.json`, records the original package spec in `.holycode-oh-my-openagent-migrated-v1.1.4`, and preserves settings, skills, and cached package data. A plugin entry added after that marker exists is treated as user-managed.

## Supply Chain

All global npm packages are first installed with lifecycle scripts disabled. `config/npm-global-script-policy.json` then validates each script-bearing package's exact version, registry integrity, architecture rule, and script body. Only the reviewed OpenCode, Claude Code, and active-architecture Paperclip PostgreSQL scripts run.

The build removes `/root/.npm` after those reviewed scripts finish. The final image therefore does not retain the root lifecycle cache, downloaded package tarballs, or stale cache metadata.

Python packages are installed from `config/python-requirements.lock`, which includes hashes for every accepted distribution. The image also carries the separately hash-locked `config/python-seed-requirements.lock` seed for pip, setuptools, Packaging, and wheel so a new `python3 -m venv` does not inherit Debian's older packaging tools.

pip 26.2 still vendors msgpack 1.1.2 and pkg_resources from setuptools 70.3.0. HolyCode replaces those two internal copies with msgpack 1.2.1 and pkg_resources from setuptools 80.9.0 using exact PyPI source hashes. The reviewed `patches/pip-vendored-pkg-resources-80.9.0.patch` keeps pip's vendored import namespace intact. The build updates pip's vendor inventory and CycloneDX BOM, then tests both the default metadata backend and the deprecated legacy backend.

GitHub CLI, fzf, and lazygit are built from exact upstream commits. Their reviewed module patches are committed under `patches/`, and the build verifies the patched module versions before tests and cross-compilation. s6-overlay, delta, and eza assets retain exact SHA-256 checks.

The final Debian package inventory is stored at `/usr/local/share/holycode/dpkg-inventory.txt` in each image and exported with the release-validation artifacts.

## Chromium And Exceptions

Both architectures install Debian Chromium and `chromium-sandbox` `150.0.7871.181-1~deb13u1`. Chromium runs as the unprivileged `opencode` user with the setuid sandbox and `config/chromium-seccomp.json` enabled. HolyCode does not use `--no-sandbox`, `SYS_ADMIN`, `seccomp=unconfined`, Google Chrome, or an architecture-specific substitute.

Debian Trixie had not published Chromium 150.0.7871.186 at release freeze. `config/security-exceptions-v1.1.4.json` therefore records exact exceptions for `CVE-2026-16804`, `CVE-2026-16805`, `CVE-2026-16806`, and `CVE-2026-16807`. Each exception:

- names the installed, available, and fixed versions
- records browser reachability and the sandbox/network controls
- expires on 08/28/2026
- must be removed as soon as Debian Trixie publishes `.186` or newer

Protected validation rejects expired, incomplete, wildcard, or unnecessary exceptions. Scanner reports are matched only against an exact, unexpired CVE, package, and installed-version tuple after the approved-source candidate check passes.

## Migration And Rollback

The release gate seeds Paperclip 2026.707.0 with a company, user membership, agents, ACP sessions, plugin ownership and configuration, Skills, custom-image settings, and active runtime state. The `v1.1.3` schema predates the connection tables, so the gate creates a tool connection and grant after migrations run, then verifies them again after restart. It upgrades only copied volumes to Paperclip 2026.722.0 and verifies migrations `0136` through `0183`, expected transformations, onboarding, Skills, OpenCode adapters, permissions, and persistence.

Rollback uses image `1.1.3` with untouched pre-upgrade volumes. Starting `1.1.3` against Paperclip data already migrated by `1.1.4` is not supported. Existing `.hermes` data remains unchanged during the upgrade test. The oh-my-openagent migration is verified separately: the legacy active entry is removed, its original spec is recorded, settings and cached data remain, and a later manual re-add remains active.

## Image And Scanner Evidence

Protected validation builds one AMD64/ARM64 candidate from the exact release commit. Native architecture jobs pull that candidate for smoke, upgrade, rollback, Chromium, Docker Scout, and Trivy gates. Publication promotes the same candidate digest to Docker Hub and GHCR instead of rebuilding it.

The pre-release source candidate produced the same fixable-finding disposition on both architectures:

| Architecture | Scanner | Critical/high total | Fixable critical/high |
|--------------|---------|---------------------|-----------------------|
| AMD64 | Docker Scout 1.23.1 | `12` across `5` packages | `0` |
| ARM64 | Docker Scout 1.23.1 | `12` across `5` packages | `0` |
| AMD64 | Trivy 0.72.0 | `337` records (`34` critical, `303` high) | `0` |
| ARM64 | Trivy 0.72.0 | `337` records (`34` critical, `303` high) | `0` |

Scanner databases classify and group Debian advisories differently, so the totals are not interchangeable. The complete SARIF/JSON reports, per-architecture SBOMs, Debian inventories, upgrade/rollback evidence, security-exception record, candidate digest, and final published manifest digest are release assets. Publication also verifies that the validated commit is the exact `origin/main` commit and that the release tag points to a commit contained in `main`. Those digests cannot be embedded in the source commit before the protected candidate exists.

Docker Scout's 12 unfixable findings are:

| Package | Findings | Reachability and disposition |
|---------|----------|------------------------------|
| Debian `perl` 5.40.1-6 | `CVE-2026-12087`, `CVE-2026-48959`, `CVE-2026-48962` | No bundled service calls the affected APIs with untrusted input; interactive-shell reachability remains. Trixie has no fixed package. |
| Debian `vim` 2:9.1.1230-2 | `CVE-2026-34982`, `CVE-2026-52860`, `CVE-2026-52858`, `CVE-2026-47162` | Interactive only; no HolyCode service invokes Vim. Trixie has no fixed package. |
| Debian `libheif` 1.19.8-1 | `CVE-2026-32740`, `CVE-2026-32882`, `CVE-2026-32741` | ImageMagick policy blocks HEIF/AVIF decoding. Trixie has no fixed package. |
| Debian `libde265` 1.0.15-1 | `CVE-2026-33164` | Pulled through libheif; the same ImageMagick policy blocks the affected decode path. Trixie has no fixed package. |
| `github.com/docker/cli` embedded in `gh` | `CVE-2025-15558` | The advisory concerns Windows Docker CLI plugin lookup. HolyCode runs the GitHub CLI on Linux, so that path is not reachable. |

This release requires zero unexcepted **fixable** critical and high findings. It does not claim zero total vulnerabilities, universal freshness, or byte-for-byte reproducibility.

## Translation Change Map

The English source changed in these translated sections:

1. Runtime pins: OpenCode 1.18.9, Claude Code 2.1.220, Paperclip 2026.722.0, npm 12.0.2, and the compatible npm/Python refresh.
2. Plugin handling: Claude Auth is packaged offline; HolyCode-managed oh-my-openagent installation is suspended and its legacy flag stops startup.
3. Removals: Netlify CLI and `serve` are no longer bundled; prior security removals remain.
4. Migration: Paperclip upgrades from 2026.707.0 to 2026.722.0; rollback requires untouched pre-v1.1.4 volumes with image `1.1.3`.
5. Browser security: Chromium `.181` keeps its sandbox; four `.186` fixes remain exact, expiring unavailable-source exceptions.

All ten translated READMEs are checked against this map before release.
