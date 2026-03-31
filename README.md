🌍 **English** | [Español](docs/translations/README.es.md) | [Français](docs/translations/README.fr.md) | [Italiano](docs/translations/README.it.md) | [Português](docs/translations/README.pt.md) | [Deutsch](docs/translations/README.de.md) | [Русский](docs/translations/README.ru.md) | [हिन्दी](docs/translations/README.hi.md) | [中文](docs/translations/README.zh.md) | [日本語](docs/translations/README.ja.md) | [한국어](docs/translations/README.ko.md)

<a name="top"></a>

# <img src="assets/logo.png" alt="HolyCode" width="39" valign="bottom"> HolyCode

<div align="center">
  <img src="assets/hero.png" alt="HolyCode Banner" width="100%" />
</div>

<p align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker Pulls](https://badgen.net/docker/pulls/coderluii/holycode?icon=docker)](https://hub.docker.com/r/coderluii/holycode)
[![Full Image](https://img.shields.io/docker/image-size/coderluii/holycode/latest?label=full&color=blue&logo=docker)](https://hub.docker.com/r/coderluii/holycode)
[![GitHub Stars](https://img.shields.io/github/stars/coderluii/holycode?style=social)](https://github.com/coderluii/holycode)
[![Twitter Follow](https://img.shields.io/twitter/follow/CoderLuii?style=social)](https://x.com/CoderLuii)
[![PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://www.paypal.com/donate/?hosted_button_id=PM2UXGVSTHDNL)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-yellow.svg?style=flat&logo=buy-me-a-coffee)](https://buymeacoffee.com/CoderLuii)
[![Website](https://img.shields.io/badge/website-coderluii.dev-orange?logo=astro)](https://coderluii.dev)
[![GitHub Release](https://img.shields.io/github/v/release/coderluii/holycode)](https://github.com/coderluii/holycode/releases)
[![Issues](https://img.shields.io/github/issues/coderluii/holycode)](https://github.com/coderluii/holycode/issues)
[![Contributors](https://img.shields.io/github/contributors/coderluii/holycode)](https://github.com/coderluii/holycode/graphs/contributors)

</p>

### One container. Every tool. Any provider.

OpenCode running in a container with everything already installed. 30+ dev tools, 10+ AI providers, headless browser, persistent state. Drop it on any machine and pick up exactly where you left off.

**Works with your Claude subscription.** Enable the Claude Auth plugin and use your existing Claude Max/Pro plan. No separate API key needed.

**Multi-agent orchestration built in.** Enable oh-my-openagent and turn OpenCode into a coordinated agent system with parallel execution.

**You were going to spend an hour getting your environment back. Or you could just `docker compose up`.**
> **Don't want to self-host?** [HolyCode Cloud](https://holycode.coderluii.dev/cloud) is coming. Same tools, zero setup. Early access is free.

---

## What is this?

You know the drill. You get your dev environment exactly right. Then you switch machines. Or rebuild a container. Or your system decides today is the day it dies.

Suddenly you're reinstalling tools. Hunting down config files. Re-entering API keys. Wondering why ripgrep isn't on PATH anymore. Figuring out why Chromium won't launch because Docker gives containers 64MB of shared memory. Then Xvfb isn't configured. Then the UID inside the container doesn't match your host and everything is permission denied.

**HolyCode is the container I built after solving every single one of those problems.**

It wraps [OpenCode](https://opencode.ai), an AI coding agent with a built-in web UI. All your settings, sessions, MCP configs, plugins, and tool history live in a bind mount outside the container. Rebuild, update, or move to a new machine. Your state comes right back.

It's the same idea as [HolyClaude](https://github.com/coderluii/holyclaude) but wrapping OpenCode instead of Claude Code. And here's the thing: OpenCode isn't locked to one provider. Point it at Anthropic, OpenAI, Google Gemini, Groq, AWS Bedrock, or Azure OpenAI. Same container, your choice of model.

30+ dev tools, two language runtimes, a headless browser stack, and process supervision. All wired up, all ready on first boot. I've been running this on my own server. Every bug has been hit, diagnosed, and fixed.

You pull it. You run it. You open your browser. You build.

---

## Table of Contents

| | Section |
|---|---------|
| 1 | [Quick Start](#-quick-start) |
| 2 | [HolyCode Cloud](#-holycode-cloud-coming-soon) |
| 3 | [Platform Support](#-platform-support) |
| 4 | [Why HolyCode](#-why-holycode) |
| 5 | [Provider Support](#-provider-support) |
| 6 | [Docker Compose - Quick](#-docker-compose---quick) |
| 7 | [Docker Compose - Full](#-docker-compose---full) |
| 8 | [Environment Variables](#-environment-variables) |
| 9 | [What's Inside](#-whats-inside) |
| 10 | [Architecture](#-architecture) |
| 11 | [CLI Usage](#-cli-usage) |
| 12 | [Data and Persistence](#-data-and-persistence) |
| 13 | [Permissions](#-permissions) |
| 14 | [Upgrading](#-upgrading) |
| 15 | [Troubleshooting](#-troubleshooting) |
| 16 | [Building Locally](#-building-locally) |
| 17 | [Contributing](#-contributing) |
| 18 | [Support](#-support) |
| 19 | [License](#-license) |

---

## 🚀 Quick Start

**Step 1.** Pull the image.

```bash
docker pull coderluii/holycode:latest
```

**Step 2.** Create a `docker-compose.yaml`.

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
      - PUID=1000
      - PGID=1000
      - ANTHROPIC_API_KEY=your-key-here
```

**Step 3.** Start it.

```bash
docker compose up -d
```

Open http://localhost:4096. You're in.

> The shipped `docker-compose.yaml` uses `${ANTHROPIC_API_KEY}` syntax which reads from your shell environment or a `.env` file. Copy `.env.example` to `.env` and fill in your API key.

<p align="right">
  <a href="#top">back to top</a>
</p>

---

## ☁ HolyCode Cloud (Coming Soon)

Don't want to self-host? We're building a managed version of HolyCode.

Same 30+ tools. Same 10+ providers. Same persistent state. No Docker. No terminal. Just open your browser and code.

**What you get with Cloud:**
- Zero setup. No Docker, no config files, no terminal commands.
- Works on any device. Laptop, tablet, phone. Open a browser and go.
- Always updated. Latest OpenCode, latest tools. We handle it.
- Your state follows you. Sessions, settings, MCP configs saved between uses.

**Early access is free.** No credit card required.

**[Claim your spot](https://holycode.coderluii.dev/cloud)**

<p align="right">
  <a href="#top">back to top</a>
</p>

---

## 💻 Platform Support

| Platform | Architecture | Status |
|----------|-------------|--------|
| Linux | amd64 | Supported |
| Linux | arm64 | Supported |
| macOS (Docker Desktop) | amd64 / arm64 | Supported |
| Windows (WSL2) | amd64 | Supported |

<p align="right">
  <a href="#top">back to top</a>
</p>

---

## ⚡ Why HolyCode

I built this because I was tired of re-doing the same setup every time. Installing OpenCode, wiring up a headless browser, fixing permission issues, debugging process supervision. Every. Time.

So I made a container that does all of it. And then I hit every possible bug so you don't have to.

| | HolyCode | DIY |
|---|----------|-----|
| Time to first working session | Under 2 minutes | 30-60 minutes |
| Chromium + Xvfb headless browser | Pre-configured | Research, install, debug yourself |
| Dev tool suite (ripgrep, fzf, lazygit, etc.) | Pre-installed | Hunt down and install one by one |
| State persistence across rebuilds | Automatic via bind mount | Manual bind mounts, easy to misconfigure |
| UID/GID file permission remapping | Built-in PUID/PGID | Dockerfile chmod hacks |
| Multi-arch support | amd64 + arm64 out of the box | Build and push both yourself |
| Updates | `docker pull` + `compose up` | Rebuild from scratch, hope nothing breaks |

<p align="right">
  <a href="#top">back to top</a>
</p>

---

## 🤖 Provider Support

OpenCode is provider-agnostic. Set whichever API key you use and you're done.

| Provider | Environment Variable | Notes |
|----------|---------------------|-------|
| Anthropic | `ANTHROPIC_API_KEY` | Claude models |
| OpenAI | `OPENAI_API_KEY` | GPT models |
| Google Gemini | `GEMINI_API_KEY` | Gemini models |
| Groq | `GROQ_API_KEY` | Fast inference |
| AWS Bedrock | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` | Set all three |
| Azure OpenAI | `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_API_VERSION` | Set all three |
| GitHub | `GITHUB_TOKEN` | GitHub Copilot via OpenAI-compatible endpoint |
| Vertex AI | (configured via OpenCode) | Google Vertex AI models |
| GitHub Models | (configured via OpenCode) | GitHub-hosted models |
| Ollama | (configured via OpenCode) | Local models via Ollama |

You only need to set keys for providers you actually use. Everything else is optional and ignored.

Vertex AI, GitHub Models, and Ollama are configured through OpenCode's provider system. Run `opencode providers login` inside the container.

<p align="right">
  <a href="#top">back to top</a>
</p>

---

## 📋 Docker Compose - Quick

The minimal setup. Copy, fill in your key, run.

```yaml
services:
  holycode:
    image: coderluii/holycode:latest
    container_name: holycode
    restart: unless-stopped
    shm_size: 2g              # Required for Chromium stability
    ports:
      - "4096:4096"           # OpenCode web UI
    volumes:
      - ./data/opencode:/home/opencode
      - ./workspace:/workspace  # Your project files
    environment:
      - PUID=1000
      - PGID=1000
      - ANTHROPIC_API_KEY=your-key-here  # Or swap for any provider key
```

<p align="right">
  <a href="#top">back to top</a>
</p>

---

## 📄 Docker Compose - Full

Every option documented. Copy to `docker-compose.yaml` and uncomment what you need.

```yaml
# HolyCode - Full Configuration Reference
# Copy this file to docker-compose.yaml and customize.
# All options documented. Uncomment what you need.

services:
  holycode:
    image: coderluii/holycode:latest
    container_name: holycode
    restart: unless-stopped
    shm_size: 2g

    ports:
      - "4096:4096"   # OpenCode web UI

    volumes:
      # --- Persistent state (all OpenCode data under home dir) ---
      - ./data/opencode:/home/opencode   # Config, sessions, plugins, cache, all XDG paths

      # --- Workspace ---
      - ./workspace:/workspace   # Your project files

    environment:
      # --- Container user ---
      - PUID=1000                # Match your host UID for file permissions
      - PGID=1000                # Match your host GID for file permissions

      # --- Git identity (used on first boot) ---
      # - GIT_USER_NAME=Your Name
      # - GIT_USER_EMAIL=you@example.com

      # --- AI provider API keys (add the ones you use) ---
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
      # - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      # - GEMINI_API_KEY=${GEMINI_API_KEY:-}
      # - GROQ_API_KEY=${GROQ_API_KEY:-}
      # - GITHUB_TOKEN=${GITHUB_TOKEN:-}

      # --- AWS Bedrock (uncomment all 3 for Bedrock) ---
      # - AWS_ACCESS_KEY_ID=
      # - AWS_SECRET_ACCESS_KEY=
      # - AWS_REGION=us-east-1

      # --- Azure OpenAI (uncomment all 3 for Azure) ---
      # - AZURE_OPENAI_ENDPOINT=
      # - AZURE_OPENAI_API_KEY=
      # - AZURE_OPENAI_API_VERSION=

      # --- OpenCode behavior (set by default in image, override if needed) ---
      # - OPENCODE_DISABLE_AUTOUPDATE=true
      # - OPENCODE_DISABLE_TERMINAL_TITLE=true
      # - OPENCODE_MODEL=claude-sonnet-4-6
      # - OPENCODE_PERMISSION=auto
      # - OPENCODE_DISABLE_LSP_DOWNLOAD=true
      # - OPENCODE_DISABLE_AUTOCOMPACT=true
      # - OPENCODE_ENABLE_EXA=true

      # --- Web UI Security (basic auth for opencode web) ---
      # - OPENCODE_SERVER_PASSWORD=your-password
      # - OPENCODE_SERVER_USERNAME=opencode

      # --- Claude Auth (use Claude subscription instead of API key) ---
      # Reads credentials from ./data/opencode/.claude/.credentials.json
      # NOTE: May violate Anthropic TOS. Use at your own risk.
      # Toggle on/off with docker compose down && up -d
      # - ENABLE_CLAUDE_AUTH=true

      # --- oh-my-openagent (multi-agent orchestration for OpenCode) ---
      # Installs automatically on first boot when enabled
      # Toggle on/off with docker compose down && up -d
      # - ENABLE_OH_MY_OPENAGENT=true
```

<p align="right">
  <a href="#top">back to top</a>
</p>

---

## 🔧 Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `PUID` | `1000` | Container user UID, match your host for correct file ownership |
| `PGID` | `1000` | Container user GID, match your host for correct file ownership |
| `GIT_USER_NAME` | `HolyCode User` | Git identity configured on first boot |
| `GIT_USER_EMAIL` | `noreply@holycode.local` | Git identity configured on first boot |
| `ANTHROPIC_API_KEY` | (none) | Anthropic Claude |
| `OPENAI_API_KEY` | (none) | OpenAI GPT models |
| `GEMINI_API_KEY` | (none) | Google Gemini |
| `GROQ_API_KEY` | (none) | Groq fast inference |
| `GITHUB_TOKEN` | (none) | GitHub CLI auth and Copilot |
| `AWS_ACCESS_KEY_ID` | (none) | AWS Bedrock - set all three AWS vars |
| `AWS_SECRET_ACCESS_KEY` | (none) | AWS Bedrock |
| `AWS_REGION` | (none) | AWS Bedrock region (e.g. `us-east-1`) |
| `AZURE_OPENAI_ENDPOINT` | (none) | Azure OpenAI - set all three Azure vars |
| `AZURE_OPENAI_API_KEY` | (none) | Azure OpenAI |
| `AZURE_OPENAI_API_VERSION` | (none) | Azure OpenAI API version |
| `OPENCODE_DISABLE_AUTOUPDATE` | `true` | Prevent OpenCode from self-updating inside the container |
| `OPENCODE_DISABLE_TERMINAL_TITLE` | `true` | Prevent OpenCode from changing the terminal title |
| `OPENCODE_MODEL` | (none) | Override the default model |
| `OPENCODE_PERMISSION` | (none) | Set to `auto` to skip permission prompts |
| `OPENCODE_DISABLE_LSP_DOWNLOAD` | (none) | Disable automatic LSP server downloads |
| `OPENCODE_DISABLE_AUTOCOMPACT` | (none) | Disable automatic context compaction |
| `OPENCODE_ENABLE_EXA` | (none) | Enable Exa web search integration |
| `OPENCODE_SERVER_PASSWORD` | (none) | Protect the web UI with basic auth |
| `OPENCODE_SERVER_USERNAME` | `opencode` | Username for web UI basic auth |
| `ENABLE_CLAUDE_AUTH` | (none) | Set to `true` to use Claude subscription instead of API key |
| `ENABLE_OH_MY_OPENAGENT` | (none) | Set to `true` to enable multi-agent orchestration plugin |

> Plugin toggles (`ENABLE_CLAUDE_AUTH`, `ENABLE_OH_MY_OPENAGENT`) take effect on container restart. Set the env var and run `docker compose down && up -d`.

> `GIT_USER_NAME` and `GIT_USER_EMAIL` are only applied on first boot. To re-apply, delete the sentinel file and restart: `docker exec holycode rm /home/opencode/.config/opencode/.holycode-bootstrapped` then `docker compose restart`.

<p align="right">
  <a href="#top">back to top</a>
</p>

---

## 📦 What's Inside

<details>
<summary><strong>Core tools</strong></summary>

| Tool | Purpose |
|------|---------|
| `git` | Version control |
| `ripgrep` | Fast file content search |
| `fd` | Fast file finder |
| `fzf` | Fuzzy finder |
| `bat` | Cat with syntax highlighting |
| `eza` | Modern ls replacement |
| `lazygit` | Terminal git UI |
| `delta` | Better git diffs |
| `gh` | GitHub CLI |
| `htop` | Process monitor |
| `tar` | Archive creation and extraction |
| `tree` | Directory tree visualization |
| `less` | Paged file viewer |
| `vim` | Terminal text editor |
| `tmux` | Terminal multiplexer |

</details>

<details>
<summary><strong>Language runtimes</strong></summary>

| Runtime | Version |
|---------|---------|
| Node.js | 22 (LTS) |
| npm | Bundled with Node.js 22 |
| Python | 3 (system) |
| pip | Bundled with Python 3 |

</details>

<details>
<summary><strong>Dev tools</strong></summary>

| Tool | Purpose |
|------|---------|
| `curl` | HTTP requests |
| `wget` | File downloads |
| `jq` | JSON processing |
| `unzip` / `zip` | Archive tools |
| `ssh` | Remote access |
| `build-essential` + `pkg-config` | Native npm addon compilation |
| `python3-venv` | Python virtual environments |
| `procps` | Process tools: ps, top |
| `iproute2` | Network tools: ip, ss |
| `lsof` | Open file diagnostics |
| OpenSSL | Crypto and cert tools (via base image) |

</details>

<details>
<summary><strong>Browser stack</strong></summary>

| Component | Purpose |
|-----------|---------|
| Chromium | Headless browser engine |
| Xvfb | Virtual framebuffer display server |
| Playwright | Browser automation framework |

The browser stack runs headless out of the box. No display server, no GPU, no extra config needed. Playwright and Puppeteer scripts work as expected.

Includes Liberation, DejaVu, Noto, and Noto Color Emoji fonts for correct page rendering and screenshots.

</details>

<details>
<summary><strong>Process management</strong></summary>

| Component | Purpose |
|-----------|---------|
| s6-overlay v3 | Process supervisor and init system |
| Custom entrypoint | UID/GID remapping, git setup, bootstrap |

s6-overlay supervises OpenCode and Xvfb. If a process crashes, it restarts automatically. Container restart policies stay clean because the supervisor handles it internally.

</details>

<p align="right">
  <a href="#top">back to top</a>
</p>

---

## 🏗 Architecture

```mermaid
graph TD
    A[docker compose up -d] --> B[entrypoint.sh]
    B --> C[UID/GID Remap]
    C --> D[Plugin Toggles]
    D --> E{First Boot?}
    E -->|Yes| F[bootstrap.sh]
    E -->|No| G[s6-overlay /init]
    F --> G
    G --> H[Xvfb :99]
    G --> I[opencode web :4096]
    I --> J[Web UI]
    J --> K[Your Browser]
    I --> L[CLI Access]
    L --> M[docker exec -it holycode bash]
    M --> N[opencode TUI]
    M --> O[opencode run 'message']
    M --> P[opencode attach localhost:4096]
```

The entrypoint handles user remapping, plugin toggles, and first-boot setup. s6-overlay supervises both Xvfb (headless display) and the OpenCode web server. If either crashes, s6 restarts it automatically. Access the web UI at port 4096 or exec into the container for the full CLI experience.

<p align="right">
  <a href="#top">back to top</a>
</p>

---

## 💻 CLI Usage

The web UI at port 4096 is the primary interface. But you can also use OpenCode directly from the command line inside the container.

### Interactive TUI

```bash
docker exec -it holycode bash
opencode
```

This opens OpenCode's full terminal UI with all the same features as the web version.

### One-shot commands

Run a single prompt without entering the TUI:

```bash
docker exec -it holycode bash -c "opencode run 'explain this codebase'"
```

### Attach to the running server

Connect a local TUI session to the already-running OpenCode web server:

```bash
docker exec -it holycode bash -c "opencode attach http://localhost:4096"
```

This shares the same session as the web UI. Changes in one appear in the other.

### Provider management

List and configure AI providers from inside the container:

```bash
docker exec -it holycode bash -c "opencode providers list"
docker exec -it holycode bash -c "opencode providers login"
```

### Useful commands

| Command | What it does |
|---------|-------------|
| `opencode` | Launch the TUI |
| `opencode run 'message'` | One-shot prompt |
| `opencode attach <url>` | Attach TUI to running server |
| `opencode web --port 4096` | Start web server (already running via s6) |
| `opencode serve` | Headless API server |
| `opencode providers list` | Show configured providers |
| `opencode providers login` | Add or switch provider |
| `opencode models` | List available models |
| `opencode models <provider>` | List models for a specific provider |
| `opencode stats` | Show token usage and costs |
| `opencode session list` | List past sessions |
| `opencode export <sessionID>` | Export session as JSON |
| `opencode plugin <module>` | Install a plugin |
| `opencode upgrade` | Upgrade OpenCode (disabled by default in container) |

<p align="right">
  <a href="#top">back to top</a>
</p>

---

## 💾 Data and Persistence

All OpenCode state lives in a single bind mount at `./data/opencode`. The container is stateless. The bind mount holds everything that matters.

| Host Path | Container Path | What's in it |
|-----------|---------------|-------------|
| `./data/opencode/.config/opencode` | `/home/opencode/.config/opencode` | Settings, agents, MCP configs, themes, plugins |
| `./data/opencode/.local/share/opencode` | `/home/opencode/.local/share/opencode` | SQLite sessions database, MCP OAuth tokens |
| `./data/opencode/.local/state/opencode` | `/home/opencode/.local/state/opencode` | Frecency data, model cache, key-value store |
| `./data/opencode/.cache/opencode` | `/home/opencode/.cache/opencode` | Plugin node_modules, auto-installed dependencies |

Rebuild the container anytime. Run `docker compose pull && docker compose up -d` and your sessions, settings, and configs come back automatically.

**SQLite WAL note.** The sessions database uses Write-Ahead Logging. Don't copy the `.db` file while the container is running. Stop the container first if you need to back up or migrate the database file.

<p align="right">
  <a href="#top">back to top</a>
</p>

---

## 🔐 Permissions

HolyCode uses `PUID` and `PGID` to remap the internal container user to match your host user. This means files written to `./workspace` are owned by you, not by root.

Find your IDs on Linux and macOS:

```bash
id -u   # PUID
id -g   # PGID
```

On most systems this is `1000:1000`. On macOS it's often `501:20`. Set them in your compose file:

```yaml
environment:
  - PUID=501
  - PGID=20
```

If you skip this, files in your workspace may be owned by root and you'll need sudo to edit them from the host.

<p align="right">
  <a href="#top">back to top</a>
</p>

---

## ⬆️ Upgrading

Pull the latest image and recreate the container. Your data stays untouched.

```bash
docker compose pull
docker compose up -d
```

That's it. One command. Your sessions, settings, and configs are in the bind mount so nothing is lost.

<p align="right">
  <a href="#top">back to top</a>
</p>

---

## 🛠 Troubleshooting

<details>
<summary><strong>Chromium crashes or browser automation fails</strong></summary>

The most common cause is not enough shared memory. Chromium needs at least 1-2 GB of `/dev/shm` to run reliably.

Make sure your compose file has `shm_size: 2g`:

```yaml
services:
  holycode:
    shm_size: 2g
```

Without this, Chromium will crash silently or produce broken screenshots.

</details>

<details>
<summary><strong>Permission denied on workspace files</strong></summary>

Your `PUID` and `PGID` don't match your host user. Find your IDs:

```bash
id -u && id -g
```

Update your compose environment section to match:

```yaml
environment:
  - PUID=1001   # replace with your actual UID
  - PGID=1001   # replace with your actual GID
```

Then recreate the container: `docker compose up -d --force-recreate`

</details>

<details>
<summary><strong>Port 4096 already in use</strong></summary>

Something else on your machine is using port 4096. Remap to a different host port:

```yaml
ports:
  - "4097:4096"   # access via http://localhost:4097
```

Or find and stop the conflicting process:

```bash
# Linux / macOS
lsof -i :4096

# Windows
netstat -ano | findstr :4096
```

</details>

<details>
<summary><strong>Container starts but web UI never loads</strong></summary>

Check the container logs:

```bash
docker compose logs -f holycode
```

OpenCode takes a few seconds to initialize. Give it 10-15 seconds after `docker compose up -d` before opening the browser. If it's still not up, the logs will tell you why.

</details>

<details>
<summary><strong>Why doesn't HolyCode need SYS_ADMIN or seccomp=unconfined?</strong></summary>

Chromium runs with `--no-sandbox` inside the container, which is standard for containerized browser setups. This eliminates the need for `SYS_ADMIN` capabilities or `seccomp=unconfined` that some other Docker browser setups require. The container itself provides the isolation boundary.

If you prefer to use Chromium's built-in sandbox instead, add the following to your compose file and remove `--no-sandbox` from the `CHROMIUM_FLAGS` environment variable:

```yaml
cap_add:
  - SYS_ADMIN
security_opt:
  - seccomp=unconfined
```

</details>

<p align="right">
  <a href="#top">back to top</a>
</p>

---

## 🔨 Building Locally

Clone the repo, build the image, swap it into your compose file.

```bash
git clone https://github.com/coderluii/holycode.git
cd holycode
docker build -t holycode:local .
```

Then in your `docker-compose.yaml` swap the image:

```yaml
image: holycode:local
```

<p align="right">
  <a href="#top">back to top</a>
</p>

---

## 🤝 Contributing

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a pull request

See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for full guidelines.

<p align="right">
  <a href="#top">back to top</a>
</p>

---

## ⭐ Support

If HolyCode saved you from another hour of environment setup, here's how to pay it forward.

- Star the repo on GitHub
- Share it with someone who'd find it useful
- [Buy Me A Coffee](https://buymeacoffee.com/CoderLuii)
- [PayPal](https://www.paypal.com/donate/?hosted_button_id=PM2UXGVSTHDNL)
- [GitHub Sponsors](https://github.com/sponsors/CoderLuii)

<p align="right">
  <a href="#top">back to top</a>
</p>

---

## 📄 License

MIT License - see [LICENSE](LICENSE).

<p align="right">
  <a href="#top">back to top</a>
</p>

---

<div align="center">

Built by [CoderLuii](https://github.com/coderluii) · [coderluii.dev](https://coderluii.dev)

</div>
