# HolyCode ⚡

**One container. Every tool. Any provider.**

OpenCode AI coding agent with built-in web UI, Claude subscription support, 50+ dev tools, a sandboxed headless browser, optional Paperclip, and external CLIProxyAPI endpoint support. Use your existing Claude Max/Pro plan. No separate API key needed.

v1.1.7 keeps the v1.1.6 toolchain and replaces npm's nested `ip-address` with 10.3.1 and PM2's nested `js-yaml` with 4.3.1. Native AMD64 and ARM64 manual checks now run Docker Scout and Trivy before a release tag is created.

[![Docker Pulls](https://img.shields.io/docker/pulls/coderluii/holycode?style=flat-square&logo=docker)](https://hub.docker.com/r/coderluii/holycode)
[![GitHub Stars](https://img.shields.io/github/stars/coderluii/holycode?style=flat-square&logo=github)](https://github.com/CoderLuii/HolyCode)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](https://github.com/CoderLuii/HolyCode/blob/main/LICENSE)

## Quick Start

Download the Chromium seccomp profile next to your Compose file:

```bash
mkdir -p config
curl -fsSLo config/chromium-seccomp.json \
  https://raw.githubusercontent.com/CoderLuii/HolyCode/v1.1.3/config/chromium-seccomp.json
```

```yaml
services:
  holycode:
    image: coderluii/holycode:latest
    container_name: holycode
    restart: unless-stopped
    shm_size: 2g
    security_opt:
      - seccomp=./config/chromium-seccomp.json
    ports:
      - "4096:4096"
      # - "3100:3100" # Paperclip dashboard
    volumes:
      - ./data/opencode:/home/opencode
      - ./local-cache/opencode:/home/opencode/.cache/opencode
      - ./workspace:/workspace
    environment:
      - ANTHROPIC_API_KEY=your-key-here
      # - ENABLE_PAPERCLIP=true
      # - PAPERCLIP_BIND=lan
      # - PAPERCLIP_ALLOWED_HOSTNAMES=192.168.1.50,my-host.local
```

```bash
docker compose up -d
# Open http://localhost:4096
```

That's it. Open your browser and start building.

## What's Inside

🤖 **OpenCode AI Agent** — Built-in web UI on port 4096. Provider-agnostic. Bring any API key.

🔑 **Claude Subscription Support** — Use your existing Claude Max/Pro plan with OpenCode. No separate API key. Toggle with `ENABLE_CLAUDE_AUTH=true`.

🧠 **Bring Your Own Multi-Agent Plugin** — HolyCode-managed oh-my-openagent installation is suspended in v1.1.4. The first flag-free start disables the old managed entry while keeping its settings, skills, and package cache.

🌐 **Headless Browser** — Chromium + Xvfb + Playwright, pre-configured for screenshots, scraping, and browser automation.

🛠️ **50+ Dev Tools:** Node.js 24.18.0 LTS with npm 12.0.2, Python 3.13 on Trixie, OpenCode 1.18.9, Paperclip 2026.722.0, eza 0.23.5, fzf 0.74.1, lazygit 0.63.1, pnpm 11.18.0, tsx 4.23.1, Vite 8.1.5, ESLint 10.8.0, Prettier 3.9.6, Wrangler 4.115.0, Prisma 7.9.1, Lighthouse 13.4.1, tqdm 4.70.0, FastAPI 0.141.1, Uvicorn 0.52.0, Claude stable 2.1.220, TypeScript 6.0.3, NumPy 2.5.1, json-server 0.17.4, git, ripgrep, bat, delta, gh CLI, and more.

TypeScript stays on 6.0.3 until the 7.x programmatic API is ready for the bundled toolchains. json-server stays on its stable 0.17.4 release. Netlify CLI, `serve`, Vercel, sharp-cli, concurrently, and LHCI are not bundled. Wrangler's removed `legacy_env` mode is not supported.

🧩 **Bundled Services** — Optional Paperclip on port 3100. Hermes is temporarily unbundled while upstream dependency fixes land; existing `.hermes` data is preserved. CLIProxyAPI integration remains available for an externally managed endpoint.

🤝 **10+ AI Providers** — Anthropic, OpenAI, Gemini, Groq, AWS Bedrock, Azure OpenAI, Vertex AI, GitHub Models, Ollama, and any OpenAI-compatible endpoint.

⚙️ **s6-overlay v3** — Process supervision with auto-restart and clean shutdown. No zombie processes.

💾 **Persistent State** — One bind mount. Sessions, settings, MCP configs, plugins all survive rebuilds.

🔒 **Permissions** — UID/GID remapping via PUID/PGID. No credentials are baked into the image; optional integrations use the local env vars and mounts you configure.

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Anthropic Claude |
| `OPENAI_API_KEY` | OpenAI |
| `GEMINI_API_KEY` | Google Gemini |
| `GROQ_API_KEY` | Groq |
| `PUID` / `PGID` | Container user UID/GID (default: 1000) |
| `ENABLE_CLAUDE_AUTH` | Use Claude subscription instead of API key |
| `ENABLE_OH_MY_OPENAGENT` | Legacy flag; `true` stops v1.1.4 while managed installation is suspended |
| `ENABLE_PAPERCLIP` | Start the Paperclip dashboard |
| `PAPERCLIP_DEPLOYMENT_MODE` | Keep Paperclip in Docker-safe authenticated mode |
| `PAPERCLIP_BIND` | Paperclip reachability preset; defaults to `lan` for Docker port publishing |
| `PAPERCLIP_ALLOWED_HOSTNAMES` | Allow comma-separated Paperclip remote hostnames/IPs, without scheme or port |
| `ENABLE_HERMES` | Legacy flag; `true` stops v1.1.4 with a migration message while Hermes is unbundled |
| `CLIPROXYAPI_ENABLED` | Add an OpenCode `cliproxyapi` provider for an external CLIProxyAPI endpoint |
| `CLIPROXYAPI_BASE_URL` | Externally managed CLIProxyAPI base URL reachable from the container |
| `CLIPROXYAPI_API_KEY` | Optional CLIProxyAPI API key env reference |
| `CLIPROXYAPI_MODEL` | Optional model key exposed as `cliproxyapi/<model>` |
| `OPENCODE_SERVER_PASSWORD` | Protect web UI with basic auth |

Paperclip defaults to `authenticated` mode with the `lan` bind preset inside HolyCode so it can bind to `0.0.0.0` and still pass upstream doctor checks in Docker.

Paperclip runs with `HOME=/home/opencode` and XDG paths under `/home/opencode`, matching the OpenCode web service. Keep your main state mount at `/home/opencode` so Paperclip's OpenCode workers read the same config as the web UI.

Paperclip now ships its Skills catalog through the package set HolyCode installs, so the Skills page loads without a HolyCode compatibility shim.

Set `PAPERCLIP_ALLOWED_HOSTNAMES` only for trusted LAN/private hostnames or IPs. Restart after changing it; hostname guard and authentication remain enabled.

Hermes is temporarily not bundled. Remove `ENABLE_HERMES=true` from older deployments before starting v1.1.4. HolyCode leaves `/home/opencode/.hermes` untouched for a future fixed release or an externally managed Hermes instance.

HolyCode-managed oh-my-openagent installation is suspended in v1.1.4. With `ENABLE_OH_MY_OPENAGENT=true`, startup stops without changing plugin state. Remove the flag and the first successful start disables the old active entry, records its package spec, and preserves its settings, skills, and package cache. Add it back manually only if you accept its current upstream dependency risk; HolyCode then treats it as user-managed.

CLIProxyAPI support is disabled by default and targets an externally managed endpoint. HolyCode does not bundle the sidecar until its release binaries have verifiable compiler provenance and pass `govulncheck`. The integration still adds a separate `cliproxyapi` provider without changing `ENABLE_CLAUDE_AUTH`, `opencode-claude-auth`, or `/home/opencode/.claude`.

## Updates and Audit Notes

When upgrading from a release before `v1.1.3`, download the Chromium seccomp profile and add it to the `holycode` service before recreating the container:

```bash
mkdir -p config
curl -fsSLo config/chromium-seccomp.json \
  https://raw.githubusercontent.com/CoderLuii/HolyCode/v1.1.3/config/chromium-seccomp.json
```

```yaml
security_opt:
  - seccomp=./config/chromium-seccomp.json
```

Then update with:

```bash
docker compose pull
docker compose up -d
```

`v1.1.4` upgrades Paperclip from 2026.707.0 to 2026.722.0. Keep untouched pre-upgrade copies of your volumes until onboarding, Skills, agents, connections, and normal provider work pass. Roll back only by restoring those copies with image `1.1.3`; do not point `1.1.3` at Paperclip data already migrated by `1.1.4`.

Tagged images pin direct npm, PyPI, and GitHub-release versions. Binary assets use checksums, container bases use digests, and GitHub Actions use commit SHAs. Claude Code is pinned to `@anthropic-ai/claude-code@2.1.220`. The supported Claude Auth plugin is included as an integrity-verified offline payload. Python packages use a hash-locked requirements file and an offline packaging-tool seed. npm lifecycle scripts are disabled during installation and validated by exact package version, integrity, architecture, and script body before approved scripts run. Debian packages resolve from current Trixie repositories at build time. User-installed plugins remain outside the image SBOM. HolyCode publishes per-platform SBOM and provenance attestations and runs per-platform vulnerability scans without claiming byte-for-byte reproducibility, universal freshness, or zero total findings.

## Links

- [GitHub](https://github.com/coderluii/holycode)
- [HolyCode Page](https://holycode.coderluii.dev)
- [HolyCode Cloud (early access)](https://holycode.coderluii.dev/cloud)
- [Full Documentation](https://github.com/coderluii/holycode#readme)
- [Podman Guide](https://github.com/CoderLuii/HolyCode/blob/main/docs/podman.md)
