# v1.3.0 release audit

This release changes validation and delivery. Top-level tool versions and compatibility holds remain those selected in the [v1.2.9 dependency audit](dependency-audit-v1.2.9.md). No new third-party patch, fork or custom build is introduced. Official Debian packages refresh for the release; the actual native inventories and scanner reports identify the installed versions.

Paperclip 2026.831.1 and jsdom 30.1.3 remain unchanged. jsdom's published `undici ^8.12.1` declaration now resolves official Undici 8.12.4; the build checks its exact version and published integrity without changing third-party code or dependency declarations. Other owner graphs remain unchanged. Fresh native AMD64 and ARM64 inventories and scanner reports cover any remaining upstream findings under the existing advisory policy.

## Release identity

The release predecessor is `v1.2.9`, pinned as `coderluii/holycode:1.2.9@sha256:3d0bdce2a62f4eb6a5b03ec644b608d2c370da143474c6c6a81474ef1a16c439`. Use one direct-main commit titled `v1.3.0`; the tag and release title must match. Preserve published tags, images and immutable assets. Do not create a release PR.

## Validation location

All source tests, builds, native runtime checks, scans, browser checks and published-artifact verification run on maintainer-controlled infrastructure. Native AMD64 and native ARM64 are both required. GitHub receives external `local/` commit statuses and release assets; it does not execute the qualification.

The retained hosted workflows are manual fallbacks. Normal push, pull-request, tag and release events do not start them. They require separate authorization for hosted execution and are not part of the normal release path. The publisher refuses an already-published release or existing version image aliases and uploads without replacing release assets.

The local status reporter binds results to the exact commit, source descriptor, run and command plan. Completed stages need verified command receipts, stream hashes and required artifacts. Failed tests report failure; interrupted, unavailable or uncertain execution reports an error. A new status does not rewrite an older cancelled Actions run. See [local validation](local-validation.md).

## Required gates

Run the full Python suite, workflow-pin/release metadata and Chromium seccomp validators, JSON/YAML checks, both Compose configurations, external-only CLIProxyAPI check and Renovate extraction under the pinned toolchain. Qualify the final committed raw source before publication; prior-release passes do not qualify a new SHA.

Build native AMD64 and native ARM64 images from that exact source. Verify the complete OCI graph, configurations, ordered filesystem IDs, first-party files, SPDX and maximum local BuildKit provenance. Run all pretag checks, protected checks and actual upgrade/persistence/rollback against untouched copies of the pinned predecessor's data.

## Security delivery policy

Retain complete Critical/High and fixable Trivy and Scout reports, secret checks, inventories and accepted upstream records for both native images. Known third-party dependency findings remain advisory under the established policy. Acceptance does not fix them or establish safety. Project-owned findings, secrets, scanner execution failures, malformed or missing reports and ambiguous identities remain blocking.

Keep the non-root user, Chromium sandbox, supplied seccomp policy and closed browser port. Avoid untrusted browser content and automation while known findings remain. The existing official Chromium security floor remains in force. Issue #14's historical closure stays tied to its actual release evidence; new findings require new image-bound results.

## Unchanged compatibility decisions

Paperclip stays at 2026.831.1, Claude Auth at 2.2.1, TypeScript at 6.0.3, json-server at 0.17.4, Apprise at 1.13.1 and Prisma at 7.10.1. Their major/beta migrations need separate compatibility and rollback work. Hermes and managed oh-my-openagent remain unavailable; existing data, settings, skills and caches remain preserved. No original-path Claude Auth token-refresh fix is claimed.

Keep persistent paths, provider credentials, external CLIProxyAPI endpoints and existing user features. The unrelated local Codex/Gemini/ttyd feature branch is outside this release.

## Publication and website

Publish the qualified graph once. Verify both registries, version aliases, release assets and exact checksums locally. Assemble a complete draft release before publishing it. A post-publication local integrity status requires actual readback; it is not a pre-merge gate. Local provenance remains local, with no invented hosted execution identity or signature.

Synchronize the separate website only after the product release is published. Preserve its design and captures, update actual release facts, run the site's full local/headless checks and upload the same qualified build. Product publication alone does not establish website deployment.
