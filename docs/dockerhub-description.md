# HolyCode ⚡

**One container. Every tool. Any provider.**

OpenCode AI coding agent with built-in web UI, Claude subscription support, 30+ dev tools, headless browser, and multi-agent orchestration. Use your existing Claude Max/Pro plan. No separate API key needed.

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
    volumes:
      - ./data/opencode:/home/opencode
      - ./workspace:/workspace
    environment:
      - ANTHROPIC_API_KEY=your-key-here
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

🛠️ **30+ Dev Tools** — Node.js 22, Python 3, git, ripgrep, fzf, bat, eza, lazygit, delta, gh CLI, tmux, and more.

🤝 **10+ AI Providers** — Anthropic, OpenAI, Gemini, Groq, AWS Bedrock, Azure OpenAI, Vertex AI, GitHub Models, Ollama, and any OpenAI-compatible endpoint.

⚙️ **s6-overlay v3** — Process supervision with auto-restart and clean shutdown. No zombie processes.

💾 **Persistent State** — One bind mount. Sessions, settings, MCP configs, plugins all survive rebuilds.

🔒 **Permissions** — UID/GID remapping via PUID/PGID. No credential proxying. Everything stays local.

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
| `OPENCODE_SERVER_PASSWORD` | Protect web UI with basic auth |

## Links

- [GitHub](https://github.com/CoderLuii/HolyCode)
- [HolyCode Page](https://holycode.coderluii.dev)
- [HolyCode Cloud (early access)](https://holycode.coderluii.dev/cloud)
- [Full Documentation](https://github.com/CoderLuii/HolyCode#readme)
