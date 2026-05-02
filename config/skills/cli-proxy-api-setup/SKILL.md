---
name: cli-proxy-api-setup
description: Configure the CLI Proxy API bundled service in HolyCode. Walks the user through choosing providers, exposing OAuth callback ports, running the right login command, verifying the proxy, and (optionally) auto-wiring OpenCode and Hermes to route through it.
---

# cli-proxy-api-setup

Use this skill when the user wants to:

- set up CLI Proxy API for the first time inside HolyCode
- log in to a new subscription provider (Claude, Codex, Gemini, Antigravity)
- toggle whether OpenCode and/or Hermes route through the proxy
- troubleshoot why a model call is not hitting the proxy

CLI Proxy API lets the user sign into Claude, Codex, Gemini and Antigravity with their **subscription accounts** and use those accounts through OpenCode (and Hermes / Paperclip workers) without exposing API keys. Tokens stay on disk under `./data/opencode/.cli-proxy-api/`.

> **Honest disclaimer:** Using subscription accounts via this proxy may violate the AI provider's terms of service depending on plan tier. Same caveat as `ENABLE_CLAUDE_AUTH`. Use at your own risk.

---

## Step 0 — Confirm the working context

1. Verify you are inside a HolyCode container or a HolyCode-backed environment.
2. Default paths used by this skill:
   - Proxy config: `~/.cli-proxy-api/config.yaml` (= `./data/opencode/.cli-proxy-api/config.yaml` on the host)
   - OpenCode config: `~/.config/opencode/opencode.json`
   - Hermes config: `~/.hermes/config.yaml`
3. If the proxy binary is not present (`command -v cli-proxy-api`), the user is on an older HolyCode image. Ask them to upgrade to the version bundling CLI Proxy API and stop.

---

## Step 1 — Detect current state

Before asking questions, summarize what is already configured:

1. Is `ENABLE_CLI_PROXY=true` in the running container? (`echo $ENABLE_CLI_PROXY`)
2. Does `~/.cli-proxy-api/config.yaml` exist?
3. Which OAuth tokens are already present? List files under `~/.cli-proxy-api/` excluding `config.yaml`.
4. Is `CLI_PROXY_AUTOWIRE` set, and to what value?
5. If `ENABLE_HERMES=true`, does `~/.hermes/config.yaml` show `model.base_url: http://localhost:8317`?

State the summary in 3-5 lines. If nothing is configured yet, this is **first-time setup**. Otherwise this run is **reconfiguration**.

---

## Step 2 — Ask which providers the user wants

Present the choices and let the user pick one or more:

1. **Claude** (Anthropic subscription) — needs OAuth callback port `54545` published.
2. **Codex** (OpenAI subscription via Codex CLI) — two options:
   - **Device-code flow** (recommended): no port needed.
   - **OAuth flow**: needs port `1455` published.
3. **Gemini** (Google AI subscription) — needs port `8085`.
4. **Antigravity** — needs port `51121`.
5. **Direct API keys only** (Claude / Gemini / Codex / OpenRouter / etc., pooled via the proxy).

If the user picks an OAuth provider, list exactly the host ports they need to expose in `docker-compose.yaml` and the published port for the proxy itself (`8317`).

---

## Step 3 — Verify compose configuration matches the chosen providers

Inspect (or ask the user to inspect) their `docker-compose.yaml`. Confirm:

1. `ENABLE_CLI_PROXY=true` is set in the `environment:` section.
2. `8317:8317` is in `ports:`.
3. The OAuth callback port for each chosen provider is in `ports:` (uncomment as needed).

If any line is missing, give them the exact diff to apply, then run:

```bash
docker compose down && docker compose up -d
```

Wait for the container to be healthy before continuing.

---

## Step 4 — Run the login command(s)

For each chosen provider, run inside the container:

| Provider     | Command (from host)                                                                                |
| ------------ | -------------------------------------------------------------------------------------------------- |
| Claude       | `docker exec -it holycode cli-proxy-api -claude-login -no-browser`                                 |
| Codex (dev)  | `docker exec -it holycode cli-proxy-api -codex-device-login`                                       |
| Codex (oauth)| `docker exec -it holycode cli-proxy-api -codex-login -no-browser`                                  |
| Gemini       | `docker exec -it holycode cli-proxy-api -login -no-browser`                                        |
| Antigravity  | `docker exec -it holycode cli-proxy-api -antigravity-login -no-browser`                            |
| Kimi         | `docker exec -it holycode cli-proxy-api -kimi-login -no-browser`                                   |

The command prints a URL. Walk the user through:

1. Copy the URL to their host browser.
2. Complete provider auth.
3. The browser is redirected to `http://localhost:<callback-port>/...`. Because the matching port is published in compose, the redirect lands inside the container and the login completes.
4. The terminal prints "Login successful" or similar. If it hangs, the most common cause is an unpublished callback port — re-check Step 3.

After success, a JSON token file appears under `~/.cli-proxy-api/`. List the directory to confirm.

---

## Step 5 — Verify the proxy is serving

From the host:

```bash
curl -s http://localhost:8317/v1/models -H "x-api-key: holycode-local" | head -40
```

The response should be a JSON object with a `data` array of models. If it returns `401`, the API key in `~/.cli-proxy-api/config.yaml` does not match `holycode-local` — either edit the config or use the right key.

Also try a Claude-protocol call to confirm the proxy is bridging protocols:

```bash
curl -s http://localhost:8317/v1/messages \
  -H "x-api-key: holycode-local" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4-5-20250929","max_tokens":50,"messages":[{"role":"user","content":"hi"}]}' | head -20
```

If Claude OAuth was completed, this should return a real response.

---

## Step 6 — Auto-wire decision

Ask the user which surfaces should automatically route through the proxy:

| Surface                           | Effect                                                                       |
| --------------------------------- | ---------------------------------------------------------------------------- |
| OpenCode (Anthropic provider)     | OpenCode's anthropic-protocol calls go to the proxy at `localhost:8317`     |
| OpenCode (OpenAI provider)        | OpenCode's openai-protocol calls go to the proxy at `localhost:8317/v1`     |
| OpenCode (Google provider)        | OpenCode's google-protocol calls go to the proxy at `localhost:8317/v1beta` |
| Hermes                            | Hermes `model.*` and `auxiliary.*` route through the proxy                  |

Then set `CLI_PROXY_AUTOWIRE` accordingly:

- `all` — wire everything (default). When `ENABLE_HERMES=true`, this includes Hermes.
- Comma-list of `opencode-anthropic`, `opencode-openai`, `opencode-google`, `hermes` — wire only the chosen surfaces.
- `false` or `none` — no auto-wire (the user manages `opencode.json` / `~/.hermes/config.yaml` themselves).

If wiring Hermes, ask which protocol it should speak to the proxy (default `anthropic`):

```bash
CLI_PROXY_HERMES_PROVIDER=anthropic   # or openai, google
```

After updating `.env` or `docker-compose.yaml`, run:

```bash
docker compose down && docker compose up -d
```

Show the resulting diffs:

- `~/.config/opencode/opencode.json` — should now contain `provider.<name>.options.baseURL` and `apiKey: "{env:CLI_PROXY_API_KEY}"` for each wired provider, plus a `_holycode_cli_proxy_managed` sentinel.
- `~/.hermes/config.yaml` (only if Hermes wired) — should contain `model.base_url: http://localhost:8317` and matching `auxiliary.*`.

---

## Step 7 — Power-user pointers

- **Edit proxy config:** `./data/opencode/.cli-proxy-api/config.yaml`. Hot-reloads on save.
- **Pool more API keys:** uncomment and fill the `claude-api-key`, `gemini-api-key`, `codex-api-key`, or `openai-compatibility` blocks in the proxy config.
- **Add model aliases:** add a `models:` list under any provider block and reference the alias from OpenCode.
- **Inspect proxy logs:** `docker logs holycode 2>&1 | grep -i cli-proxy`.
- **Disable auto-wire without losing your edits:** the `_holycode_cli_proxy_managed` sentinel makes off-toggling clean — entrypoint only reverts keys it set.

---

## Rules

- Do not invent provider names that are not supported by the upstream binary.
- Do not store API keys in `opencode.json` directly — always use `{env:CLI_PROXY_API_KEY}` substitution.
- If the user has hand-edited `opencode.json` and the `_holycode_cli_proxy_managed` sentinel is missing, do not silently overwrite their `provider.*.options.baseURL` — explain the conflict and ask first.
- Always remind the user about the TOS disclaimer before they run their first OAuth login.
- Keep responses short. Show the exact command, not a paragraph about it.
