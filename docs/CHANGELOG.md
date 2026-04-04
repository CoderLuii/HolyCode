# Changelog

All notable changes to HolyCode will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.4] - 04/04/2026

### Added

- Ship a built-in `/oh-my-openagent-setup` skill for first-time setup and reruns after provider changes (only visible when `ENABLE_OH_MY_OPENAGENT=true`)
- Copy HolyCode-managed OpenCode skills into `~/.config/opencode/skills` on boot without overwriting existing user skill folders
- Ensure enabled plugin packages are installed on boot if they are missing from the OpenCode cache
- Add `HOLYCODE_PLUGIN_UPDATE` environment variable with two modes: `manual` (install if missing only) and `auto` (install if missing and update on boot)

### Changed

- Document `/oh-my-openagent-setup` as the supported path for writing `oh-my-openagent.jsonc`
- Document the default picker policy so only Sisyphus, Hephaestus, Prometheus, and Atlas are visible by default
- Clarify that `OPENCODE_DISABLE_AUTOUPDATE` only affects OpenCode itself, not plugins
- Clarify that `/oh-my-openagent-setup` skill only appears when the plugin is enabled

### Fixed

- Add an explicit rerun + doctor + model-capability refresh path for stale visible default-model behavior after provider changes

## [1.0.2] - 04/03/2026

### Changed

- Clarify that `/home/opencode` is the fixed container path while the host data path depends on the bind mount the user chooses
- Clarify that main data can live on remote storage while the cache path should remain local
- Clarify that `ENABLE_OH_MY_OPENAGENT=true` enables the plugin through `opencode.json` without promising a separate plugin-specific config file on the host

## [1.0.1] - 04/02/2026

### Fixed

- Detect CIFS/SMB network mounts and warn about SQLite WAL incompatibility
- Add `nobrl,mfsymlinks` mount option documentation for README Troubleshooting section

### Changed

- Expand SQLite WAL note with network storage guidance
- Add startup check in entrypoint.sh for CIFS/SMB detection
- Replace the `holycode-cache` named volume guidance with an explicit local-path cache bind mount for CIFS/SMB setups

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
