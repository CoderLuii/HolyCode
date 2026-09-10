# HolyCode v1.2.0 Dependency Audit

Date: 09/10/2026

Git predecessor `v1.1.9` is the supported release baseline. Upgrade and rollback validation must use `coderluii/holycode:1.1.9@sha256:06344a7b42b4938959c8913687d57a1fbbf65a18a11864bab3fca95d3b9b801c`.

This audit records the frozen v1.2.0 dependency decisions and release policy. Every release must pass native AMD64/ARM64 runtime checks, upgrade/rollback fixtures, SBOM/provenance generation, and Trivy and Docker Scout gates against the final commit and exact image digest before publication.

## Adopted

| Component | Version | Source or validation anchor |
| --- | --- | --- |
| Node.js | 24.21.0 LTS | Official image index pinned to `sha256:db3ae80f5d8df06e04dabdf7b44cbf008d32de168205fa0294444aabbc08c590`; [release](https://github.com/nodejs/node/releases/tag/v24.21.0) |
| OpenCode / Claude Code | [1.18.30](https://www.npmjs.com/package/opencode-ai/v/1.18.30) / [2.1.268](https://www.npmjs.com/package/@anthropic-ai/claude-code/v/2.1.268) | Exact npm pins with frozen registry integrity and upstream tag commits; lifecycle and native-owner execution are required release gates |
| OpenSpec | [1.13.0](https://www.npmjs.com/package/@fission-ai/openspec/v/1.13.0) | MIT; npm provenance present; telemetry stays disabled and project initialization remains explicit with `openspec init --tools opencode` |
| Vite / Wrangler | [8.3.0](https://www.npmjs.com/package/vite/v/8.3.0) / [4.131.0](https://www.npmjs.com/package/wrangler/v/4.131.0) | Exact npm pins with provenance; Wrangler's Miniflare/workerd/native payload and Sharp AVIF checks are required release gates |
| pip vendored msgpack | [1.2.2](https://github.com/msgpack/msgpack-python/releases/tag/v1.2.2) | PyPI source SHA-256 `9eb0b0e602064527a045ea28c4f174ed69383587e29cebe28947e3b84106eb2a`; stays inside pip's vendored namespace |
| Renovate validator | [44.79.2](https://github.com/renovatebot/renovate/releases/tag/44.79.2) | Validation-only AGPL-3.0 package; not bundled in the runtime image; strict configuration and dependency extraction checked under Node 24.21.0 |
| FontTools | [4.65.0](https://github.com/fonttools/fonttools/releases/tag/4.65.0) | Matplotlib-owned transitive dependency; regenerated hash lock; Python 3.13 wheels for AMD64 and ARM64; font parsing/rendering is a required image gate |

## Unchanged and held

Paperclip remains at 2026.831.1, so v1.2.0 adds no Paperclip migration. Its owner-scoped Undici 6.28.1 compatibility replacement remains in place. TypeScript stays at 6.0.3 to preserve the `tsserver` and stable programmatic compiler API contract. Prisma stays on stable 7.10.0, json-server stays on stable 0.17.4, pyee stays on compatible 13.0.1, and PM2 keeps its owner-scoped js-yaml 4.3.2 replacement.

pnpm remains at 12.4.0 as an explicit hold. The official npm package exists with registry SLSA provenance and the upstream GitHub release is non-prerelease, but npm's mutable `latest` and `latest-12` tags resolve to 12.3.4. HolyCode does not downgrade to 12.3.4 or adopt the 12.4.1 prerelease. The existing preinstall/postinstall block and reviewed native/offline hydration path remain subject to runtime and native validation.

## Owner-specific dependency controls

| Owner | Dependency disposition | Required result |
| --- | --- | --- |
| PM2 7.0.4 | js-yaml -> 4.3.2 | Exact PM2 owner declaration, integrity, dependency tree, YAML parse, and PM2 process smoke |
| Prisma 7.10.0 | deepmerge-ts -> 8.0.2; mysql2 -> 3.24.4 | Exact owner declarations, integrity checks, dependency trees, and Prisma/API smokes |
| Wrangler 4.131.0 / Miniflare 5.20260910.0-alpha | Upstream-owned Sharp 0.35.4 with libvips 1.3.3; no HolyCode replacement | Exact owner and architecture payload checks, `npm ls`, libvips identification, AVIF round trip, and no global Sharp CLI |
| Paperclip 2026.831.1 | Undici -> 6.28.1 | Exact Connect 1.x owner guards, integrity, dependency tree, and runtime request smoke |
| pip 26.2.1 | vendored msgpack -> 1.2.2 | Source hash, vendored import path, API, pure-Python fallback, malformed-input, and pip operation checks |

Replacement rows stay scoped to the named owner graph. They are not top-level global tools and must fail closed if upstream metadata no longer matches the frozen precondition. Wrangler's Sharp row records an upstream-owned dependency verified in place; HolyCode does not rewrite it.

## Lifecycle, rollback, and release policy

npm packages install with scripts disabled. The release process must check exact versions, registry and packed-byte integrity, architecture, owner declarations, and approved script bodies before running only the reviewed lifecycle steps. OpenSpec must not mutate projects at startup and must keep telemetry disabled. Claude Code 2.1.268 synthetic-auth startup and marketplace/path-containment regression coverage are required release gates through `scripts/smoke_image.sh`; no live account, provider, OAuth, or billing claim follows from these synthetic fixtures or the frozen metadata.

Because Paperclip is unchanged, v1.2.0 requires no new migration instructions. Users must stop the container and preserve untouched home, local-cache, and workspace volume backups before upgrading. Rollback means restoring those untouched backups with image `1.1.9`; the rollback fixture must not reuse volumes that v1.2.0 has already started against. The older v1.1.9 Paperclip migration and v1.1.8 rollback instructions remain in the historical documentation.

Release clearance requires clean native AMD64 and ARM64 builds, runtime/plugin and persisted upgrade/rollback checks, deny-by-default lifecycle validation, per-platform SBOM/provenance, and valid Trivy and Docker Scout fixable Critical/High gates on the final release image. A passing fixable gate does not mean the image has zero vulnerabilities; unfixed findings remain visible. Any image-affecting edit invalidates earlier image evidence.

This audit is not a general legal-compliance audit. Packaged license/source notices are in [`THIRD-PARTY-NOTICES`](../THIRD-PARTY-NOTICES) and must match the copy installed at `/usr/local/share/holycode/THIRD-PARTY-NOTICES` before release.
