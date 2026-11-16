# Dependency correction background

## Paperclip-owned Cursor SDK 1.4.0

The first native validation of the simplified workflow stopped on both AMD64 and ARM64: the existing Paperclip adapter resolved Cursor SDK 1.4.0, while HolyCode expected 1.3.1. Paperclip 2026.831.1 declares `@cursor/sdk ^1.0.28`; the new minor version satisfies that published declaration. This was dependency resolution drift, not a runner or workflow permission failure.

The correction updates HolyCode's expected SDK version, official tarball integrity, selected-manifest fixture and third-party notice. Paperclip, jsdom 30.1.3 and Undici 8.12.4 remain unchanged. No package source, dependency declaration or upstream manifest is patched, and no obsolete subtree is forced into the install.

Local Linux verification under Node 24.22.2 and npm 12.2.2 installed the official Paperclip package with lifecycle scripts disabled. Its actual owner graph, SDK API/type exports, missing-key adapter diagnostic and Undici resolution checks passed. All 432 installed SDK payload files matched the integrity-verified official tarball. These checks do not replace native AMD64/ARM64 image/runtime/scanner/rollback qualification.

The version guard still rejects an unexpected SDK version. Keep that strict check: changing the expectation requires official package integrity and consumer compatibility evidence, not merely a newer registry version. Before another expensive native build, check owner-graph changes under the pinned package manager in a disposable prefix.

This correction passed native validation before v1.3.1 release preparation. Published v1.3.0 images, assets and historical dependency audits remain unchanged. The [v1.3.1 audit](dependency-audit-v1.3.1.md) records the new release scope and required source-bound native qualification. Earlier validation samples do not qualify a changed release image.
