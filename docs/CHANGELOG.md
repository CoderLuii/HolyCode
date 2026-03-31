# Changelog

All notable changes to HolyCode will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] - 03/30/2026

### Added
- OpenCode AI coding agent (v1.3.6) with built-in web UI on port 4096
- s6-overlay v3 for process supervision with auto-restart and clean shutdown
- Headless browser: Chromium + Xvfb + Playwright for browser automation
- Single bind mount persistence (all state under ./data/opencode)
- UID/GID remapping via PUID/PGID environment variables
- First-boot bootstrap with default config and git identity setup
- Claude Auth plugin toggle (ENABLE_CLAUDE_AUTH) for Claude subscription users
- oh-my-openagent plugin toggle (ENABLE_OH_MY_OPENAGENT) for multi-agent orchestration
- Web UI basic auth support (OPENCODE_SERVER_PASSWORD)
- 30+ dev tools: git, ripgrep, fd, fzf, bat, eza, lazygit, delta, gh CLI, htop, tmux, and more
- Language runtimes: Node.js 22, Python 3
- 10+ AI provider support: Anthropic, OpenAI, Gemini, Groq, AWS Bedrock, Azure OpenAI, Vertex AI, GitHub Models, Ollama
- CI/CD pipeline for Docker Hub + GHCR (amd64 + arm64)
- Docker Compose quick-start and full reference configurations
- Comprehensive README with quick start, troubleshooting, and architecture docs
- Landing page at holycode.coderluii.dev
