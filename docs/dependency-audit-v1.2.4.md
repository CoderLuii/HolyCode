# HolyCode v1.2.4 Dependency Audit

Date: 10/01/2026

Git predecessor `v1.2.3` is the supported release baseline. Upgrade and rollback validation uses `coderluii/holycode:1.2.3@sha256:b46cf61c33f3b7556b7bc165ebfa9dabfff66753a134d832ee8ec118c6354083`, the verified Docker Hub and GHCR index with two native platforms and two attestations.

This records the selected v1.2.4 source graph. It does not claim the release has shipped. The native AMD64 and native ARM64 images, installed notices, runtime modes, scanners, SBOMs, provenance, registry aliases, and rollback still need validation against one final candidate.

## Selected updates

| Component | v1.2.3 | v1.2.4 source selection | Boundary |
| --- | ---: | ---: | --- |
| [OpenCode](https://registry.npmjs.org/opencode-ai/1.18.34) | 1.18.32 | 1.18.34 | Exact npm payload and reviewed lifecycle script |
| [Claude Code](https://registry.npmjs.org/%40anthropic-ai%2Fclaude-code/2.1.286) | 2.1.281 | 2.1.286 | Exact npm payload, native payload, legal notice, and synthetic startup checks |
| [OpenSpec](https://registry.npmjs.org/%40fission-ai%2Fopenspec/1.14.0) (`@fission-ai/openspec`) | 1.13.2 | 1.14.0 | Explicit `openspec init`; telemetry disabled |
| [npm](https://registry.npmjs.org/npm/12.2.0) | 12.1.0 | 12.2.0 | Existing owner-scoped fixes and lifecycle policy retained |
| [pnpm](https://registry.npmjs.org/pnpm/12.8.1) | 12.6.0 | 12.8.1 | Exact package and approved install-script body |
| [Vite](https://registry.npmjs.org/vite/8.3.2) | 8.3.1 | 8.3.2 | Existing esbuild consumer checks retained |
| [Wrangler](https://registry.npmjs.org/wrangler/4.145.0) | 4.138.0 | 4.145.0 | Declares Miniflare 5.20260930.0-alpha, workerd 1.20260930.2, and esbuild 0.28.1 |
| [GitHub CLI](https://github.com/cli/cli/releases/tag/v2.102.0) | 2.101.0 | 2.102.0 | Signed upstream commit `fc4b137cdef0a6bd28fd461b7cf9c84a5812a8cd`, rebuilt from source |
| [Go builder](https://hub.docker.com/_/golang) | 1.27.1-trixie prior index | 1.27.1-trixie `sha256:3b77fc618ec235a1ab412de7737f120dd507c57e8d87de4cbb7994fb94275ed5` | Same index in all three source builders |
| [Renovate](https://registry.npmjs.org/renovate/44.129.0) | 44.112.3 | 44.129.0 | CI validator only; not a bundled runtime package |
| [Trivy](https://github.com/aquasecurity/trivy/releases/tag/v0.75.0) | 0.74.0 | 0.75.0 | Official AMD64 and ARM64 asset checksums in both workflows |
| [Docker Scout](https://github.com/docker/scout-cli/releases/tag/v1.26.0) | 1.24.0 | 1.26.0 | Official AMD64 and ARM64 asset checksums in both workflows |

Node 24.21.0 retains the official Trixie-slim index `sha256:8ec5d7557396cfe32d21c3f9c13072355ceab22b584578ca4bb28af31120cffe`. The October 1 Debian refresh changes build-time distro resolution; it does not create a byte-for-byte reproducibility claim.

## Owner-scoped graph

| Owner | Selected dependency | Decision |
| --- | --- | --- |
| Paperclip 2026.831.1 Cursor adapter | `@cursor/sdk` 1.0.35 | Adapter declares `^1.0.28`; the resolved SDK no longer declares `@connectrpc/connect-node` |
| Paperclip server / jsdom 30.1.1 | Undici 8.11.2 | jsdom declares `^8.10.2`; one Undici and no Connect Node transport remain in the clean graph |
| Prisma 7.10.0 | mysql2 3.24.5 | Integrity-bound owner replacement and `@types/node` peer/API checks retained |
| Prisma 7.10.0 | deepmerge-ts 8.0.2 | Existing owner replacement retained |
| Prisma / mysql2 | `@types/node` 20.19.43 and `undici-types` 6.21.0 | Type-only peer and declaration payloads remain in Prisma scope |
| npm 12.2.0 | `brace-expansion` 5.0.12, `tar` 7.5.22, `ip-address` 10.7.2 | Existing integrity-bound owner replacements retained |
| npm 12.2.0 / node-gyp | node-gyp 13.0.2 and Undici 8.11.2 | npm's declared `node-gyp ^13.0.0` permits 13.0.2; the replacement declares `undici ^8.4.1` |
| PM2 7.0.4 | js-yaml 4.3.2 | Existing v4-compatible replacement retained |
| PM2 7.0.4 / get-uri 6.0.5 | basic-ftp 6.2.1 | Narrow replacement under get-uri; separate FTP transfer hosts remain disabled by default |
| Miniflare 5.20260930.0-alpha | Sharp 0.35.4 / libvips 1.3.3 | Upstream owner declaration and binary/API checks retained |
| pip 26.2.1 | vendored msgpack 1.2.2 and pkg_resources from setuptools 78.1.1 | Existing hash-verified replacements retained |
| pip 26.2.1 | vendored urllib3 2.8.0 | Re-generated with pip's own vendoring configuration and patches; product urllib3 lock stays unchanged |

The v1.2.3 Paperclip image carried a reviewed Undici 6.28.1 overlay because its then-resolved Cursor SDK installed Connect's Node transport. A clean install now resolves SDK 1.0.35 under Paperclip's unchanged range. That SDK removed the transport, and jsdom owns the only Undici at 8.11.2. The former overlay targeted a package that is no longer present and failed the candidate build. v1.2.4 removes the obsolete overlay instead of adding an unused transport or downgrading jsdom. Exact registry integrity, installed owner declarations, one-Undici/no-Connect counts, `npm ls --omit=dev --all`, packaged Cursor/Agent method shape, no-key adapter result, and a loopback jsdom URL fetch are gates. Authenticated Cursor `me`, models, create, resume, send, getRun, and wait calls are unavailable without credentials; they are not reported as passed.

The unpublished pre-tag candidate at commit `272576373624b4240c9231c8d7b6a1525831bde8` failed run `36901198681` on three different owners. npm's node-gyp 13.0.0 pulled Undici 6.28.0; PM2's get-uri 6.0.5 pulled basic-ftp 5.3.1; pip's internal vendor bundle contained urllib3 2.7.0 even though the separate product lock already selected 2.8.0. The corrected source keeps each replacement under its owner and does not add a scanner exception. npm's node-gyp and Undici tarballs are bound to registry SHA-512 integrities `sha512-SXTvw3PxznpowYhJSOD9mVQBgDaCTWXffX+wQZsQ7PbcTV86TsXCUcSZhHnskFQvrvn/OdSzJPMsptT2pIj9ww==` and `sha512-u4UB2/IrKdU6lFxumHmmo1a3fCQO5tzQllRorfoRS63txhrB7xTpSn1PftwC4qEHkOaqP95fCWW4lJzwErwzhQ==`. PM2's basic-ftp tarball is bound to `sha512-bK67isD+lKq46AU8vNtjvMaT2ZqAOAmNCbxUHlFBRD4k15NWxyEjmaKtZPlgce58So4BNTjITGQOVTjL9y0ECA==`.

The owner regressions exercise consumers, not only version text. `scripts/test_node_gyp_download.mjs` uses a local headers/SHASUMS endpoint, and `scripts/test_node_gyp_native.mjs` compiles and loads a small N-API addon through npm's offline default node-gyp path. `scripts/test_get_uri_ftp.mjs` drives get-uri FTP download, encoded names, missing and cached files, MDTM/LIST fallback, and a malformed LIST response; the transfer-host check confirms that a PASV address cannot redirect the client to a separate host by default. Those tests use local fixtures and no real credentials. They do not establish compatibility with arbitrary external FTP servers or native addons.

### pip vendoring provenance

The pip source is upstream commit `634a6ec1a5d9dcc2433571cdb2f4c58a4bb29caf` for 26.2.1. Its `pyproject.toml` vendoring configuration has SHA-256 `ded7555c0b1455d9e6911796566dfb815b3a02e2eb14a388d9c193b47027f77d`. The three upstream patches are `urllib3-disable-brotli.patch` (`28c5c54c565b95c0c3583c91a00b62eeedf5d807e4aba32a2f5c2518afc9d9ef`), `urllib3-fix-emscripten-import.patch` (`6d6174dde794ab5f8754d6c8bc6b6d59e045d1b9b48685fc5a4aee06a01a9eeb`), and `urllib3.patch` (`ac960bc57e4cdb4e8495e4ec442daba1eb4e50998ff6f125ed3c33afa729e197`). The upstream urllib3 2.8.0 wheel is SHA-256 `0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3`.

Two independent clean pip checkouts ran the same [vendoring 1.4.0](https://pypi.org/project/vendoring/1.4.0/) procedure: set the `urllib3` requirement in `src/pip/_vendor/vendor.txt` to 2.8.0, then run `vendoring update urllib3` and `vendoring sync` at the source root. All three pip patches applied in both runs. The normalized generated urllib3 subtree is in the candidate source as `patches/pip-vendored-urllib3-2.8.0.tar.gz`, SHA-256 `c64eb33b95a5cbd0afd35cadfb3778da6e7c979efa634312f39a392ca3cb11f2`; the generated BOM is `patches/pip-vendored-bom-26.2.1-urllib3-2.8.0.cdx.json`, SHA-256 `4e645472781870c87c896be33c1c3e0f93b2f8efeaf8ef780f629cad7d960e75`. Both outputs matched byte-for-byte across those two runs. The build starts from that generated BOM, then updates only the existing HolyCode msgpack and pkg_resources component references and copies their verified license files. `scripts/verify_pip_vendor_record.py` refreshes and verifies the repaired paths in pip's installed `RECORD`, while preserving unrelated original entries. Complete `RECORD` coverage and hashes remain a separate final-image acceptance check. This is a documented downstream repair, not a claim that the final installed pip is byte-identical to upstream pip.

To reproduce the archive from either clean checkout after `vendoring sync`, run the following from `src/pip/_vendor` with GNU tar 1.35 and gzip 1.12 (the generator used here):

```sh
tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner -cf - urllib3 | gzip -n > pip-vendored-urllib3-2.8.0.tar.gz
sha256sum pip-vendored-urllib3-2.8.0.tar.gz bom.cdx.json
```

The tar command sorts paths, fixes uid/gid and mtime to zero, and retains generated source file modes. `gzip -n` omits the original filename and timestamp. The BOM is the byte-for-byte `src/pip/_vendor/bom.cdx.json` output of `vendoring sync`, not a separately normalized rewrite. Both independent generated checkouts reproduced the pinned archive and BOM hashes with this command.

The hash-locked upstream pip wheel remains the input in `config/python-seed-requirements.lock`, but the offline cache carries a deterministic repaired derivative. `scripts/rebuild_pip_seed_wheel.py` verifies the upstream wheel SHA-256 `71138adf1f4ca900cdb7d289c21b7494329f2332b6d85f0e1c42108c0384ed3e`, replaces only the three repaired vendor subtrees plus their pip-owned licenses and metadata, and refreshes and verifies their wheel `RECORD` entries while carrying unrelated upstream entries through. The derived wheel must be installed in a fresh venv with the four existing seed packages; that venv runs the pip consumer and repaired-path metadata fixtures. Its derivative SHA-256 is an output of the final native builds, not the upstream lock hash. Both architecture builds must independently verify all wheel `RECORD` entries and coverage, and agree on the derivative and installed bytes before publication.

`scripts/test_pip_vendor_urllib3.py` covers pip's vendored Requests adapter, local authenticated index/install/download, offline wheel and PEP 517 build, direct TLS trust and certificate/hostname failures, HTTP and HTTPS proxy paths with separate target/proxy TLS contexts and forwarding, and exact bounded rejection of an oversized chunk header through both `read_chunked` and `stream`. These are local, credential-free fixtures. The original candidate's urllib3 2.7.0 accepted the oversized header and timed out; the repaired 2.8.0 fixture rejects it. The separate product `urllib3==2.8.0` remains unchanged.

Prisma's type-only peer remains @types/node 20.19.43, with undici-types 6.21.0 declarations beside it. Neither becomes a top-level runtime tool. Drizzle ORM 0.45.3 is a fixture-only compatibility dependency, not a new top-level image tool. Lighthouse 13.5.0 still owns `@paulirish/trace_engine 0.0.65`, whose literal latest declarations resolve to `third-party-web 0.30.0` and `legacy-javascript 0.0.1`. The bounded global npm diagnostic checks those two known findings; it is not a universal clean-tree claim. Paperclip's Skills catalog remains package data: 16 local entries with 27 verified local files and one optional pinned remote descriptor with 79 metadata records.

## Unchanged tools and compatibility holds

TypeScript 6.0.3, Prisma 7.10.0, json-server 0.17.4, Paperclip 2026.831.1, `opencode-claude-auth 2.2.1`, Python direct inputs and both hash locks remain unchanged. No new bundled service, provider mode, or top-level dependency is introduced. HolyCode-managed oh-my-openagent and Hermes stay suspended; CLIProxyAPI remains an externally managed endpoint. Netlify CLI, `serve`, Vercel, sharp-cli, concurrently, and LHCI remain outside the image.

| Component | Retained | Evaluated alternative | Unlock condition |
| --- | ---: | ---: | --- |
| Paperclip | 2026.831.1 | 2026.916.1 | An upstream-supported narrow self-hosted control preserves explicit user choices for the native-runner default, then passes fresh, upgrade, and native checks |
| TypeScript | 6.0.3 | 7.0.2 | Deliberate compiler API and `tsserver` migration with editor fixtures |
| Prisma | 7.10.0 | 8.0.0-rc.19 | Stable compatible 8.x plus database, client, migration, and owner-scoped replacement fixtures |
| json-server | 0.17.4 | 1.0.0-beta.15 | Stable 1.x plus CLI and CRUD fixtures |
| PM2-owned js-yaml | 4.3.2 | 5.4.2 | PM2 owner/API check and YAML fixture for a v5 change |
| Paperclip/jsdom Undici | 8.11.2 | 6.29.0 overlay | Obsolete overlay removed; keep the resolved jsdom owner graph and loopback consumer gate |
| Python locks | v1.2.3 direct and transitive hashes | New resolver output | Released upstream pip-tools correction and clean supported Linux regeneration |

The Python locks were accepted with Python 3.13.15, pip 26.2.1, pip-tools 7.6.1, and resolver-only Click 8.4.2. Product `click==8.5.0` is unchanged. pip-tools still writes a false `--no-index` header when its updater resolves that product Click version. Automatic pip-tools lock updates are therefore still blocked pending the upstream [issue #2472](https://github.com/jazzband/pip-tools/issues/2472) fix in [PR #2475](https://github.com/jazzband/pip-tools/pull/2475); no local header workaround is shipped.

`opencode-claude-auth 2.2.1` stays bundled offline, but [issue #11](https://github.com/CoderLuii/HolyCode/issues/11) remains open. Its reported proactive credential-refresh failure has no failing-before/passing-after reproduction or reporter-confirmed recovery. Claude Code synthetic-auth startup and marketplace/path-containment regression coverage are required release gates through `scripts/smoke_image.sh`; no live account, provider, OAuth, or billing claim follows from those fixtures. The plugin advertises Claude `ccVersion` 2.1.280; no incompatibility with 2.1.286 has been demonstrated, and no live OAuth or expiry test is claimed.

Paperclip 2026.831.1 adds no migration or native-runner default override in this bundle. No supported narrow self-hosted control preserves explicit user choices on the evaluated 2026.916.1 line. Untouched v1.2.3 home, cache, and workspace backups remain the rollback boundary.

## Notices and release gates

`THIRD-PARTY-NOTICES` records redistributed package notices, including the Cursor SDK's terms-bound license, without claiming legal clearance. The final AMD64 and ARM64 images must prove installed notice byte equality and architecture-specific payload, version, and license evidence. The Node/Go base and Debian package inventories must be checked from the built artifacts. Renovate, scanner binaries, and test-only Drizzle ORM are not runtime notice entries.

The unpublished pre-tag run `36917367504` installed `chromium`, `chromium-common`, and `chromium-sandbox` `154.0.8037.57-1~deb13u1` on ARM64 while AMD64 fetched `154.0.8037.92-1~deb13u1`. A fresh Trixie Security ARM64 package-index check on `2026-10-01` still lists `.57` for all three packages. Debian DSA-6535-1 publishes `.92` as the corrected source version, but a compatible `.92` ARM64 binary is not available yet.

`config/security-exceptions-v1.2.4.json` records exactly 33 package/CVE/version tuples: 11 reviewed CVEs for each of the three `.57` packages, bound only to release `v1.2.4` and platform `linux/arm64`, approved by CoderLuii on `2026-10-01`, and expiring on `2026-10-08`. The native workflows refresh the installed and available versions for all three packages from the disposable candidate image before applying the record. A compatible fixed candidate uses no exception. AMD64, another release, another package version, an expired record, a new finding, a secret finding, or an available fixed ARM64 candidate fails closed. Raw Trivy and Docker Scout reports remain release evidence, and workflow summaries state whether 33 or zero exceptions were applied.

Chromium opens user-requested content, including untrusted web content, and several reviewed findings may permit code execution outside the sandbox. Avoid untrusted web content and browser automation on ARM64 until the corrected package is installed. The unprivileged `opencode` user, setuid sandbox, constrained seccomp profile, and lack of a public browser port remain required, but this mitigation does not make the known vulnerabilities safe or unreachable. Rebuild with `154.0.8037.92-1~deb13u1` or newer and remove the exception as soon as Debian publishes compatible ARM64 packages.

Source tests and policy validators are candidate checks. Publication still requires native AMD64 and native ARM64 builds and complete smoke; runtime/plugin modes, issue #12 discovery fixtures, upgrade/restart/untouched-volume rollback, listeners and activation; installed inventories and notices; per-platform SBOM, provenance/attestations, raw Trivy and Docker Scout reports with exact exception accounting; release-asset checksums; and final Docker Hub/GHCR digest and alias verification. This is not a zero-vulnerability claim. Any Dockerfile, policy, or notice change invalidates earlier image evidence. This audit does not claim the release has shipped.
