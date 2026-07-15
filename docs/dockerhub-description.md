# HolyCode ⚡

**One container. Every tool. Any provider.**

OpenCode AI coding agent with built-in web UI, Claude subscription support, 50+ dev tools, headless browser, bundled Hermes + Paperclip integrations, and external CLIProxyAPI endpoint support. Use your existing Claude Max/Pro plan. No separate API key needed.

v1.1.2 migrates the image to Debian Trixie with Python 3.13, npm 12.0.1, and NumPy 2.5.1. It also refreshes OpenCode to 1.18.2, Wrangler to 4.111.0, and lazygit to 0.63.1. Release tags use exact `vX.Y.Z`; Docker image tags drop the `v` prefix. Every version segment is one digit: `v1.0.9` rolls to `v1.1.0`, `v1.1.9` to `v1.2.0`, and `v1.9.9` to `v2.0.0`.

[![Docker Pulls](https://img.shields.io/docker/pulls/coderluii/holycode?style=flat-square&logo=docker)](https://hub.docker.com/r/coderluii/holycode)
[![GitHub Stars](https://img.shields.io/github/stars/coderluii/holycode?style=flat-square&logo=github)](https://github.com/CoderLuii/HolyCode)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](https://github.com/CoderLuii/HolyCode/blob/main/LICENSE)

## Quick Start

```yaml
services:
  holycode:
    image: coderluii/holycode:latest
    container_name: holycode
    restart: unless-stopped
    shm_size: 2g
    ports:
      - "4096:4096"
      # - "3100:3100" # Paperclip dashboard
      # - "8642:8642" # Hermes API server
    volumes:
      - ./data/opencode:/home/opencode
      - ./local-cache/opencode:/home/opencode/.cache/opencode
      - ./workspace:/workspace
    environment:
      - ANTHROPIC_API_KEY=your-key-here
      # - ENABLE_PAPERCLIP=true
      # - PAPERCLIP_BIND=lan
      # - PAPERCLIP_ALLOWED_HOSTNAMES=192.168.1.50,my-host.local
      # - ENABLE_HERMES=true
      # - API_SERVER_KEY=replace-with-a-real-secret
```

```bash
docker compose up -d
# Open http://localhost:4096
```

That's it. Open your browser and start building.

## What's Inside

🤖 **OpenCode AI Agent** — Built-in web UI on port 4096. Provider-agnostic. Bring any API key.

🔑 **Claude Subscription Support** — Use your existing Claude Max/Pro plan with OpenCode. No separate API key. Toggle with `ENABLE_CLAUDE_AUTH=true`.

🧠 **Multi-Agent Orchestration** — Enable oh-my-openagent for parallel execution, specialized agents, and background tasks. Toggle with `ENABLE_OH_MY_OPENAGENT=true`.

🌐 **Headless Browser** — Chromium + Xvfb + Playwright, pre-configured for screenshots, scraping, and browser automation.

🛠️ **50+ Dev Tools:** Node.js 24.18.0 LTS with npm 12.0.1, Python 3.13 on Trixie, OpenCode 1.18.2, Paperclip 2026.707.0, Hermes v2026.7.7.2, eza 0.23.5, fzf 0.74.0, lazygit 0.63.1, pnpm 11.13.0, tsx 4.23.1, Vite 8.1.4, ESLint 10.7.0, Prettier 3.9.5, Wrangler 4.111.0, Netlify CLI 26.2.0, tqdm 4.68.4, uvicorn 0.51.0, Claude stable 2.1.210, TypeScript 6.0.3, NumPy 2.5.1, json-server 0.17.4, git, ripgrep, bat, delta, gh CLI, Prisma, and more.

TypeScript stays on 6.0.3 until the 7.x programmatic API is ready for the bundled toolchains. json-server stays on its stable 0.17.4 release, and Vercel stays on 54.21.0 until authenticated personal and team/scope behavior is proven. Wrangler's removed `legacy_env` mode is not supported.

🧩 **Bundled Services** — Optional Hermes Agent on port 8642 and Paperclip on port 3100. CLIProxyAPI integration remains available for an externally managed endpoint.

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
| `ENABLE_OH_MY_OPENAGENT` | Enable multi-agent orchestration |
| `ENABLE_PAPERCLIP` | Start the Paperclip dashboard |
| `PAPERCLIP_DEPLOYMENT_MODE` | Keep Paperclip in Docker-safe authenticated mode |
| `PAPERCLIP_BIND` | Paperclip reachability preset; defaults to `lan` for Docker port publishing |
| `PAPERCLIP_ALLOWED_HOSTNAMES` | Allow comma-separated Paperclip remote hostnames/IPs, without scheme or port |
| `ENABLE_HERMES` | Start Hermes API + messaging bridge |
| `API_SERVER_KEY` | Required when Hermes API server is enabled |
| `CLIPROXYAPI_ENABLED` | Add an OpenCode `cliproxyapi` provider for an external CLIProxyAPI endpoint |
| `CLIPROXYAPI_BASE_URL` | Externally managed CLIProxyAPI base URL reachable from the container |
| `CLIPROXYAPI_API_KEY` | Optional CLIProxyAPI API key env reference |
| `CLIPROXYAPI_MODEL` | Optional model key exposed as `cliproxyapi/<model>` |
| `OPENCODE_SERVER_PASSWORD` | Protect web UI with basic auth |

Paperclip defaults to `authenticated` mode with the `lan` bind preset inside HolyCode so it can bind to `0.0.0.0` and still pass upstream doctor checks in Docker.

Paperclip runs with `HOME=/home/opencode` and XDG paths under `/home/opencode`, matching the OpenCode web service. Keep your main state mount at `/home/opencode` so Paperclip's OpenCode workers read the same config as the web UI.

Paperclip now ships its Skills catalog through the package set HolyCode installs, so the Skills page loads without a HolyCode compatibility shim.

Set `PAPERCLIP_ALLOWED_HOSTNAMES` only for trusted LAN/private hostnames or IPs. Restart after changing it; hostname guard and authentication remain enabled.

Hermes exposes an API service. Set `API_SERVER_KEY` before enabling it. A `404` from `/` is normal as long as the process is healthy and port `8642` is listening.

CLIProxyAPI support is disabled by default and targets an externally managed endpoint. HolyCode no longer bundles the sidecar while the `v7.2.77` image contains fixable high-severity Go findings. The integration still adds a separate `cliproxyapi` provider without changing `ENABLE_CLAUDE_AUTH`, `opencode-claude-auth`, or `/home/opencode/.claude`.

## Updates and Audit Notes

Update with:

```bash
docker compose pull
docker compose up -d
```

Tagged images pin direct npm, PyPI, and GitHub-release versions. Binary assets use checksums, container bases use digests, and GitHub Actions use commit SHAs. Claude Code is pinned to `@anthropic-ai/claude-code@2.1.210`. npm lifecycle scripts are denied by default and checked against a reviewed version-and-script policy. Debian packages resolve from current Trixie repositories at build time, and boot-installed OpenCode plugins are live registry installs outside the image SBOM. Netlify CLI is limited to remote build/deploy commands; its local functions binaries are removed. HolyCode publishes per-platform SBOM and provenance attestations and runs per-platform vulnerability scans without claiming byte-for-byte reproducibility, zero vulnerabilities, or universal freshness.

## Links

- [GitHub](https://github.com/coderluii/holycode)
- [HolyCode Page](https://holycode.coderluii.dev)
- [HolyCode Cloud (early access)](https://holycode.coderluii.dev/cloud)
- [Full Documentation](https://github.com/coderluii/holycode#readme)
- [Podman Guide](https://github.com/CoderLuii/HolyCode/blob/main/docs/podman.md)
