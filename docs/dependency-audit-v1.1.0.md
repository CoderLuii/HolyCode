# v1.1.0 Dependency Audit

Audit date: 07/12/2026

This release checked each direct version pin against its upstream stable registry or release feed immediately before the release build. A newer version was adopted only after the image and service checks passed. Compatibility holds remain explicit instead of being presented as current.

## Adopted

| Component | v1.1.0 | Evidence |
|-----------|--------|----------|
| Node.js and npm | 24.18.0 LTS / 11.16.0 | [Node.js release](https://nodejs.org/en/blog/release/v24.18.0) |
| OpenCode | 1.17.18 | [npm](https://www.npmjs.com/package/opencode-ai) |
| Claude Code | 2.1.207 | [npm](https://www.npmjs.com/package/@anthropic-ai/claude-code) |
| Paperclip | 2026.707.0 | [npm](https://www.npmjs.com/package/paperclipai) |
| Hermes | v2026.7.7.2 at commit `b7751df34688835a108e0d630f3495fc11f3df79` | [GitHub releases](https://github.com/NousResearch/hermes-agent/releases) |
| CLIProxyAPI | v7.2.71 at manifest `sha256:5f94c3ef20b55c00a8ca6608038d22d9371c656fde039538f09788aab68a87fe` | [Docker Hub tags](https://hub.docker.com/r/eceasy/cli-proxy-api/tags) |
| eza / fzf / lazygit / delta / s6-overlay | 0.23.5 / 0.74.0 / 0.63.0 / 0.19.2 / 3.2.3.0 | Upstream GitHub releases, with downloaded assets checked by SHA-256 |
| pnpm / Vite / ESLint / Prettier | 11.12.0 / 8.1.4 / 10.7.0 / 3.9.5 | npm stable versions |
| Wrangler / Netlify CLI | 4.110.0 / 26.2.0 | npm stable versions |
| tqdm / Uvicorn | 4.68.4 / 0.51.0 | PyPI stable versions |
| OpenCode plugin defaults | `opencode-claude-auth` 2.0.0 / `oh-my-openagent` 4.17.0 | npm stable versions |

The remaining exact npm and Python pins in the Dockerfile also matched their stable registry versions on the audit date. That includes Playwright, requests, HTTPX, Beautiful Soup, lxml, Pillow, openpyxl, python-docx, pandas, matplotlib, seaborn, rich, click, Apprise, Jinja, PyYAML, python-dotenv, Markdown, FastAPI, tsx, esbuild, serve, nodemon, concurrently, dotenv-cli, PM2, Prisma, Drizzle Kit, Lighthouse, LHCI, sharp-cli, and http-server.

## Held

| Component | Held version | Reason |
|-----------|--------------|--------|
| TypeScript | 6.0.3 | TypeScript 7.0.2 does not expose the stable programmatic API expected by several bundled toolchains. |
| NumPy | 2.4.6 | NumPy 2.5.1 requires Python 3.12 or newer; Debian Bookworm supplies Python 3.11. |
| json-server | 0.17.4 | The newer 1.0.0 release remains a beta. |
| Vercel | 54.21.0 | Vercel 55.0.0 requires authenticated scope/team validation that was not available to public or no-secret CI. |

The held versions stay under Renovate review. They are not described as latest in release documentation.

## Removed Or Replaced

- Replaced Debian's older fzf package with the checksum-verified upstream 0.74.0 binary.
- Removed Drizzle Kit's unused `@esbuild-kit/esm-loader` dependency and resolved its runtime through the tested esbuild 0.28.1 pin.
- Removed floating Claude installation and floating automatic plugin updates.

## Scanner Disposition

The AMD64 candidate was scanned after the final dependency build. Trivy 0.72.0 reported 34 critical and 449 high findings. Of the critical findings, 29 are Debian Bookworm packages without a repository fix. The other five are Go standard-library findings in Netlify CLI 26.2.0's `@netlify/local-functions-proxy-linux-x64@1.1.1` binary.

Docker Scout 1.23.1 evaluated the SPDX inventory against Docker's advisory data and reported 7 critical and 103 high rules across 26 vulnerable packages. Its SARIF output contains 116 package-level results for those 110 rules because some rules apply to more than one package occurrence. Six critical rules apply to the same Netlify local proxy binary, including `CVE-2025-22871`, which Trivy does not classify in its five-finding critical set. The remaining critical rule is the unfixed Debian Perl `CVE-2026-12087`. Scout found no remaining Drizzle Kit `@esbuild-kit` or nested esbuild critical path after the installation-layer cleanup.

Netlify's current stable package still resolves that platform binary to 1.1.1, and no newer compatible platform package is published. `.trivyignore.yaml` therefore lists only those five CVEs, the exact AMD64 and ARM64 binary paths, the reason, and an expiration date of 08/12/2026. The complete report remains visible in protected validation, while the fixable-critical gate applies the reviewed exception and blocks every other fixable critical finding.

Trivy's secret scanner initially matched 12 placeholder GitHub tokens inside an npm package archive under `/root/.npm/_cacache`. Those strings were documentation examples, not credentials, but the cache had no runtime purpose. The final image removes root's npm cache inside each global-install layer instead of suppressing the findings; protected validation keeps both vulnerability and secret scanning enabled. The rebuilt AMD64 candidate reports zero secret findings.

Release images publish per-platform SBOM and provenance attestations. Docker Scout and Trivy both run for AMD64 and ARM64 before image publication. The protected workflow creates an SPDX file from each tested image for Scout because indexing a second local copy of the large image can exhaust GitHub-hosted runner disk. It downloads the exact Scout 1.23.1 release binary, verifies its published SHA-256, and writes SARIF from that inventory. Trivy still scans the image directly for the complementary report and fixable-critical gate. Scanner counts are evidence from a dated database snapshot, not a promise that the image has zero vulnerabilities.
