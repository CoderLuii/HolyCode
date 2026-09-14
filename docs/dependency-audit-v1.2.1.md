# HolyCode v1.2.1 Dependency Audit

Date: 09/14/2026

Git predecessor `v1.2.0` is the supported release baseline. Upgrade and rollback validation must use `coderluii/holycode:1.2.0@sha256:72085db834a1ac2de07629abfeb8c9972296a40f3a0903fbd35d54155553f1c6`.

This audit records the frozen v1.2.1 candidate decisions. Publication remains gated on a final notice-bound candidate, native AMD64 and native ARM64 runtime/plugin/upgrade checks, per-platform SBOM and provenance, and Trivy and Docker Scout policy results for the exact release digest. Preparatory AMD64 checks do not satisfy those final gates.

## Adopted

| Component | Version | Validation boundary |
| --- | --- | --- |
| Node.js / Go | 24.21.0 LTS / 1.27.1 | Existing digest-pinned official image indexes remain frozen for Linux AMD64 and ARM64 |
| Claude Code | 2.1.270 | Exact npm integrity, reviewed unchanged lifecycle body, native payload ownership, synthetic startup, and both target architectures remain required image gates |
| OpenSpec | `@fission-ai/openspec` 1.13.0 | Telemetry stays disabled; project initialization remains explicit with `openspec init --tools opencode` |
| pnpm | 12.4.1 | Exact npm integrity with lifecycle scripts blocked; both native payloads and offline execution remain required image gates |
| Wrangler / Miniflare / workerd | 4.131.2 / 5.20260911.1-alpha / 1.20260911.1 | Owner-bound graph; workerd is not a new direct pin; exact package owners, installed copies, binaries, and both architectures must match |
| fzf / lazygit | 0.74.4 / 0.65.1 | Built from commits `a140afeb4d733cad3c96a56bf6db7e26853b6757` and `17cb09fa7b08bc96d9f0e81b91f4720fc1a36700`; source/module and runtime checks remain mandatory |
| Matplotlib / tqdm / Uvicorn | 3.11.2 / 4.70.1 / 0.53.0 | Hash-locked Python 3.13 packages; Matplotlib needs native wheel/runtime proof on both architectures |
| Renovate validator | 44.87.1 | Validation-only through the existing npm/npx path; not installed in the image |

## Python lock provenance

The accepted locks were generated locally with Python 3.13.15, pip 26.2.1, pip-tools 7.6.1, and Click 8.4.2. pip-tools emitted the natural canonical headers without `--no-index`, `--reuse-hashes`, masking, or hand editing. Click 8.4.2 is resolver-only; the product package `click==8.5.0` remains unchanged in the application lock.

Renovate 44.87.1 can parse the accepted headers, but repository configuration cannot constrain the Click version inside Renovate's pip-tools environment. A future automated artifact update can still resolve Click 8.5.0 and regenerate the invalid `--no-index` header. Automated Python lock maintenance is therefore not fully validated and remains blocked pending an upstream pip-tools fix or separately authorized control of the external resolver environment. No wrapper, manager disablement, global setting, or product dependency workaround was added.

## Holds and known limits

These alternatives were evaluated on 09/14/2026. They are not claims about mutable registry tags.

| Component | Retained | Evaluated | Compatibility risk | Upgrade condition |
| --- | --- | --- | --- | --- |
| TypeScript | 6.0.3 | 7.0.2 | The major migration is unproven for tsserver and programmatic compiler API consumers | Both interfaces and existing consumers pass |
| Prisma | 7.10.0 | 8.0.0-rc.15 | A direct release candidate is excluded | A stable compatible release plus database, client, and migration fixtures pass |
| json-server | 0.17.4 | 1.0.0-beta.15 | A direct beta is excluded | A stable compatible release plus CLI and CRUD fixtures pass |
| PM2-owned js-yaml | 4.3.2 | 5.4.2 | A major replacement needs owner and API compatibility | Owner and API checks plus the PM2 YAML process fixture pass |
| Paperclip-owned Undici | 6.28.1 | 8.10.2 | A major replacement needs Connect and Paperclip compatibility | Owner checks plus streaming, error, and request fixtures pass |

Paperclip remains at 2026.831.1 with Undici 6.28.1, so v1.2.1 adds no Paperclip migration. `opencode-claude-auth 2.2.0` remains bundled.

This release does not claim to fix authentication. The reported Claude Auth lock defect still has unresolved concurrency races, and endpoint differences do not prove a server rejection. Existing manual, auto, and disabled plugin-update policies remain unchanged.

Claude Code synthetic-auth startup and marketplace/path-containment regression coverage are required release gates through `scripts/smoke_image.sh`; no live account, provider, OAuth, or billing claim follows from those fixtures.

Prisma's owner-scoped mysql2 3.24.4 replacement now includes its non-optional, type-only peer `@types/node 20.19.43` and the exact `undici-types 6.21.0` declaration dependency in Prisma's package scope. Neither declaration payload is fetched or resolved by a package manager: both are raw-extracted only after registry SRI and downloaded-byte verification. The pre-existing mysql2-scoped runtime dependency installation remains in place. Final rebuilt-image evidence remains a release gate.

The complete global npm diagnostic is allowed to report only two version- and owner-bound findings: Lighthouse 13.4.1 owns `@paulirish/trace_engine 0.0.65`, whose literal `latest` declarations resolve to `third-party-web 0.29.2` and `legacy-javascript 0.0.1`. The smoke check rejects missing peers and every changed or additional problem. This is not a universal clean-tree claim, and the third-party manifests and moving tags remain untouched. Drizzle ORM is used only by a test fixture and is not installed as a global runtime dependency.

## Release gates

Release clearance requires the final candidate to pass native AMD64 and native ARM64 builds; complete smoke, plugin-mode, and exact v1.2.0 upgrade/rollback checks; license/notice and inventory review; per-platform SBOM and provenance; and Trivy and Docker Scout fixable Critical/High policy gates. Unfixed distro findings remain visible, so a passing fixable gate is not a zero-vulnerability claim. Any image-affecting or notice-affecting edit invalidates earlier candidate evidence.

This audit is not a general legal-compliance audit. Packaged license/source notices are in [`THIRD-PARTY-NOTICES`](../THIRD-PARTY-NOTICES) and must match the copy installed at `/usr/local/share/holycode/THIRD-PARTY-NOTICES` before release.
