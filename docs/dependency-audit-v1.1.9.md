# HolyCode v1.1.9 Dependency Audit

Date: 09/08/2026

Git predecessor `v1.1.8` is the supported release baseline. Upgrade and rollback validation uses `coderluii/holycode:1.1.8@sha256:9e7748ce057082f6e8168ac9e6e5434234cf601927b412f49a09b0de992d901c`.

## Adopted

| Component | Version | Source or validation anchor |
| --- | --- | --- |
| Node.js / Go | 24.20.0 LTS / 1.27.1 | Official image indexes pinned to `sha256:50c3b2f6988dfc307b86e5301d69611af31f4789bdf232863b07d3b02fe55ae0` and `sha256:9baa6b4187bbb98d240372a8a235ac0bb6b5ddd52bba1431dc2f7c0705862728` |
| GitHub CLI | 2.100.0 | [Release](https://github.com/cli/cli/releases/tag/v2.100.0), commit `45437bc7eeeb3359bbfddd1742f79de7652fd3e2` |
| fzf / lazygit | 0.74.3 / 0.65.0 | fzf commit `15f64c492a08f0840b81540c7d1de35737448086`; lazygit commit `c07f4d381b90419583b7ce04f87379654d983ebc` |
| OpenCode / Claude Code | [1.18.29](https://www.npmjs.com/package/opencode-ai/v/1.18.29) / [2.1.265](https://www.npmjs.com/package/@anthropic-ai/claude-code/v/2.1.265) | Exact npm pins; reviewed lifecycle scripts and architecture payloads |
| OpenSpec / Claude Auth | [1.12.0](https://www.npmjs.com/package/@fission-ai/openspec/v/1.12.0) / [2.2.0](https://www.npmjs.com/package/opencode-claude-auth/v/2.2.0) | OpenSpec telemetry disabled; explicit `openspec init --tools opencode`; Claude Auth installed from an integrity-verified offline payload |
| Paperclip | [2026.831.1](https://www.npmjs.com/package/paperclipai/v/2026.831.1) | [Migration release](https://github.com/paperclipai/paperclip/releases/tag/v2026.831.0); owner-scoped Undici 6.28.1 compatibility replacement |
| pnpm / ESLint / Wrangler | [12.4.0](https://github.com/pnpm/pnpm/releases/tag/v12.4.0) / [10.10.0](https://www.npmjs.com/package/eslint/v/10.10.0) / [4.130.0](https://www.npmjs.com/package/wrangler/v/4.130.0) | Exact package pins and deny-by-default lifecycle policy |
| Python direct updates | NumPy 2.5.3 / lxml 6.1.3 | Hash-locked application requirements; resolved pydantic-core 2.46.5 and pyee 13.0.1 |

## Unchanged and held

Node.js remains on the 24.20.0 LTS line. npm 12.0.2, tsx 4.23.13, Vite 8.2.2, Prettier 3.9.6, Prisma 7.10.0, Lighthouse 13.4.1, json-server 0.17.4, PM2 7.0.4, s6-overlay 3.2.3.2, delta 0.19.2, eza 0.23.5, fzf 0.74.3, and the unchanged Python inputs retain their exact pins.

TypeScript remains at 6.0.3 because TypeScript 7 removes the `tsserver` command and changes the stable programmatic API surface used by bundled toolchains. Prisma remains on stable 7.10.0 instead of the 8.0 release candidate. json-server remains on stable 0.17.4 instead of the 1.0 beta. Paperclip stays on the compatible Undici 6.28.1 line rather than changing its Connect 1.x owner graph to Undici 8. pyee remains at resolved 13.0.1 rather than the incompatible 14.x candidate.

The application keeps pip 26.2.1 and Click 8.5.0. The isolated lock-generation helper used Python 3.12, pip 25.0.1, Click 8.4.2, and pip-tools 7.6.1; that helper-only Click hold prevents pip-tools from treating `--no-index` as enabled. It is not a product dependency downgrade.

## Owner-specific replacements

| Owner | Replaced package | Enforced result |
| --- | --- | --- |
| npm 12.0.2 | brace-expansion 5.0.9, tar 7.5.22, ip-address 10.7.0 | Exact owner declarations, integrity, installed trees, and CLI runtime |
| PM2 7.0.4 | js-yaml 4.3.1 -> 4.3.2 | Exact PM2 owner rewrite, packed-byte SHA-512 verification, `npm ls`, YAML parse, and PM2 process smoke |
| Prisma 7.10.0 | deepmerge-ts 7.1.5 -> 8.0.2; mysql2 3.15.3 -> 3.24.4 | Exact owner rewrites, integrity checks, dependency trees, and Prisma/API smokes |
| Wrangler 4.130.0 / Miniflare 5.20260908.0-alpha | Sharp 0.35.2 -> 0.35.4; target libvips 1.3.1 -> 1.3.3 | Exact Miniflare owner rewrite, architecture payloads, `npm ls`, libheif 1.23.2, AVIF round trip, and no global Sharp CLI |
| Paperclip 2026.831.1 | Undici -> 6.28.1 | Exact Connect 1.x owner guards, integrity, dependency tree, and runtime request smoke |

These replacements are scoped to the named owner graph. They are not top-level global tools and fail closed if upstream metadata no longer matches the frozen precondition.

## Lifecycle, migration, and release policy

npm packages install with scripts disabled. The image checks exact versions, registry and packed-byte integrity, architecture, owner declarations, and approved script bodies before running only the reviewed lifecycle steps. pnpm 12.4.0 keeps its preinstall/postinstall scripts blocked and uses the reviewed native/offline hydration path. OpenSpec never mutates a project at startup and keeps telemetry disabled. Claude Auth stays bundled for offline installation. Renovate 44.69.12 validates the frozen dependency extraction rules.

Paperclip 2026.831.1 adds migrations `0223` through `0230`. Migration `0224` resets transient in-progress adapter login sessions, `0225` removes the retired Claude setup-token session table, `0229` removes `brandColor` and `attachmentMaxBytes`, and `0230` adds account issuer values. Users must stop the container and back up home/workspace volumes before upgrading, restart login after migration, and retain the untouched backup until their persisted app data and provider credentials pass validation. Rollback means restoring that untouched backup with image `1.1.8`; image `1.1.8` must not run against a migrated `v1.1.9` database.

The release workflow requires native AMD64 and ARM64 builds, runtime/plugin and migration checks, deny-by-default lifecycle validation, per-platform SBOM/provenance, and fixable Critical/High Trivy and Docker Scout gates before promotion. A passing fixable gate does not mean the image has zero vulnerabilities; unfixed findings remain visible. The immutable release commit does not embed changing run numbers or image digests. After publication, exact commit, run, digest, SBOM, scanner, and attestation evidence will be available with the [v1.1.9 release assets](https://github.com/CoderLuii/HolyCode/releases/tag/v1.1.9).

Local AMD64 validation passed the final image build, runtime and plugin checks, seeded migration, restart, untouched-backup rollback, and both fixable scanner gates with zero findings and zero exceptions. The 64-test Python suite also passed. These local checks do not replace the required native architecture release gates bound to the final commit and protected candidate digest.

This audit records the build inputs and enforced release policy. It is not a general legal-compliance audit; packaged license/source notices are in [`THIRD-PARTY-NOTICES`](../THIRD-PARTY-NOTICES) and inside the image at `/usr/local/share/holycode/THIRD-PARTY-NOTICES`.
