# HolyCode v1.1.8 Dependency Audit

Date: 09/01/2026

Git predecessor `v1.1.7` is the only supported release baseline. Upgrade and rollback validation uses the verified published image `coderluii/holycode:1.1.7@sha256:4e20d9eac20afb4e779b98037a923201027008f0acee5617fe10cbf90f1a4a41`.

## Adopted

| Component | Version | Validation anchor |
| --- | --- | --- |
| Node.js / Go | 24.20.0 / 1.27.0 | Official images pinned by OCI digest |
| GitHub CLI / fzf / lazygit | 2.98.0 / 0.74.3 / 0.64.1 | Exact upstream tags and commits rebuilt from source |
| OpenCode / Claude Code | 1.18.25 / 2.1.252 | Exact npm pins and reviewed lifecycle scripts |
| @fission-ai/openspec | 1.11.0 | Exact npm pin, telemetry disabled, explicit non-root offline initialization smoke |
| Paperclip | 2026.824.1 | Runtime, persistence, plugin, and upgrade checks |
| pnpm / tsx / Vite | 11.25.0 / 4.23.13 / 8.2.2 | Exact npm pins |
| Wrangler / Prisma / ESLint | 4.127.1 / 7.10.0 / 10.9.1 | Exact npm pins and lifecycle policy entries |
| Trivy / Docker Scout | 0.74.0 / 1.24.0 | Architecture-specific checksum-bound downloads |

Python direct inputs moved to wheel 0.48.0, lxml 6.1.2, click 8.5.0, apprise 1.13.1, python-dotenv 1.2.3, and Uvicorn 0.52.4. Both Python locks were regenerated with Python 3.12 and pip-compile using their recorded commands.

The deny-by-default lifecycle policy records both the direct esbuild 0.28.2 CLI and Wrangler 4.127.1's exact nested esbuild 0.28.1 dependency. Both packaged platform binaries remain script-blocked during installation and are exercised by the image validation path.

The native scanner pass identified four fixable transitive inputs before publication. GitHub CLI 2.98.0 is rebuilt after updating `golang.org/x/mod` from 0.38.0 to 0.40.0, Prisma 7.10.0's nested `deepmerge-ts` 7.1.5 and `mysql2` 3.15.3 payloads are replaced with the integrity-verified 8.0.0 and 3.22.0 releases, and Debian's `python3-pip` bootstrap path is not installed because it pulls `python3-setuptools` 70.3.0 into image history. A temporary standard-library virtual environment now installs the hash-locked `/usr/local` pip 26.2.1 and setuptools 84.0.0 payloads directly. The full GitHub CLI tests, Prisma dependency-tree and runtime checks, Python metadata and `pip check`, and both architecture scanner gates validate these remediations.

## Holds and removals

TypeScript remains at 6.0.3, Paperclip's reviewed Undici replacement remains at 6.28.0, PM2's direct js-yaml dependency is validated at 4.3.1, and pnpm remains on npm's stable 11.x line. These are compatibility holds, not claims that no newer major exists.

pip 26.2.1 still vendors `pkg_resources` from advisory-flagged setuptools 70.3.0. HolyCode replaces only that vendored copy with checksum-bound setuptools 78.1.1 source, updates pip's vendored dependency metadata, and validates both pip's default importlib metadata backend and the compatibility backend. The expired Chromium exception file is not used by either workflow; the release remains blocked unless both native architectures pass the fail-closed fixable critical and high scanner gates.
