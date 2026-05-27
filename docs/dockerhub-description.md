# HolyCode ⚡

**One container. Every tool. Any provider.**

OpenCode AI coding agent with built-in web UI, Claude subscription support, 50+ dev tools, headless browser, bundled Hermes + Paperclip integrations, and optional CLIProxyAPI sidecar support. Use your existing Claude Max/Pro plan. No separate API key needed.

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
      # - PAPERCLIP_ALLOWED_HOSTNAMES=192.168.1.50,my-host.local
      # - ENABLE_HERMES=true
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

🛠️ **50+ Dev Tools** — Node.js 22, Python 3, git, ripgrep, fzf, bat, eza, lazygit, delta, gh CLI, pnpm, TypeScript, Prisma, and more.

🧩 **Bundled Services** — Optional Hermes Agent on port 8642, Paperclip on port 3100, and CLIProxyAPI sidecar support in the full Compose profile. Flip an env var, restart, and they come up beside OpenCode.

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
| `PAPERCLIP_ALLOWED_HOSTNAMES` | Allow comma-separated Paperclip remote hostnames/IPs, without scheme or port |
| `ENABLE_HERMES` | Start Hermes API + messaging bridge |
| `CLIPROXYAPI_ENABLED` | Add optional OpenCode `cliproxyapi` provider for a CLIProxyAPI sidecar |
| `CLIPROXYAPI_BASE_URL` | CLIProxyAPI base URL, usually `http://cliproxyapi:8317/v1` in full Compose |
| `CLIPROXYAPI_API_KEY` | Optional CLIProxyAPI API key env reference |
| `CLIPROXYAPI_MODEL` | Optional model key exposed as `cliproxyapi/<model>` |
| `OPENCODE_SERVER_PASSWORD` | Protect web UI with basic auth |

Paperclip defaults to `authenticated` mode inside HolyCode so it can bind to `0.0.0.0` and still pass upstream doctor checks in Docker.

Set `PAPERCLIP_ALLOWED_HOSTNAMES` only for trusted LAN/private hostnames or IPs. Restart after changing it; hostname guard and authentication remain enabled.

Hermes exposes an API service. A `404` from `/` is normal as long as the process is healthy and port `8642` is listening.

CLIProxyAPI support is disabled by default and lives in the full Compose profile. It adds a separate `cliproxyapi` provider without changing `ENABLE_CLAUDE_AUTH`, `opencode-claude-auth`, or `/home/opencode/.claude`.

## Links

- [GitHub](https://github.com/coderluii/holycode)
- [HolyCode Page](https://holycode.coderluii.dev)
- [HolyCode Cloud (early access)](https://holycode.coderluii.dev/cloud)
- [Full Documentation](https://github.com/coderluii/holycode#readme)
- [Podman Guide](https://github.com/CoderLuii/HolyCode/blob/main/docs/podman.md)
