# HolyCode v1.1.6 Dependency Audit

This release starts from Git commit `038e4ac1d2c47a48237245877618d28299e256d6` and predecessor image `coderluii/holycode:1.1.5@sha256:804ec668b97466dba9a26ded8af258fabc2d778047b7c8aebdaab7bccd9a3ae8`.

## Accepted updates

| Component | Version | Release control |
|---|---:|---|
| Node.js | 24.19.0 | Official image pinned by digest |
| GitHub CLI | 2.97.0 | Exact upstream tag and commit |
| fzf | 0.74.2 | Exact upstream tag and commit |
| lazygit | 0.64.0 | Exact upstream tag and commit |
| OpenCode | 1.18.16 | npm integrity and lifecycle-script policy |
| Claude Code | 2.1.228 | npm integrity and lifecycle-script policy |
| Claude Auth | 2.1.6 | Integrity-verified offline payload |
| pnpm / tsx / Vite | 11.21.0 / 4.23.12 / 8.2.1 | Exact npm pins |
| Wrangler / ESLint | 4.121.0 / 10.8.1 | Exact npm pins |
| Playwright / NumPy | 1.62.0 / 2.5.2 | Hash-locked Python requirements |
| Packaging / setuptools / pip | 26.3 / 84.0.0 / 26.2.1 | Hash-locked runtime and offline seed |
| Docker Scout / Trivy | 1.24.0 / 0.73.0 | Exact release checksums and workflow pins |

Paperclip remains at `2026.722.0` with its reviewed Undici `6.28.0` replacement. pip keeps vendored msgpack `1.2.1` and pkg_resources from setuptools `80.9.0`.

## Deferred update

TypeScript 7.0.2 is deferred. HolyCode retains TypeScript 6.0.3 because the 7.x programmatic toolchain compatibility gate is not established for every bundled consumer. This hold does not block the independently validated updates above.

## Architecture and scanner gates

Pull requests build and smoke-test native `linux/amd64` and `linux/arm64` images. The tagged-release workflow regenerates per-platform SBOMs and runs current Docker Scout and Trivy data against the exact candidate digest. Scanner databases can change after this audit, so the remote fail-closed result remains authoritative.
