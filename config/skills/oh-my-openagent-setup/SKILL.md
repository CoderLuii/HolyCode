---
name: oh-my-openagent-setup
description: Configure or reconfigure oh-my-openagent for HolyCode. Mirrors the upstream provider questionnaire, writes plugin config, keeps only primary agents visible, and prints doctor/refresh/auth follow-up steps.
---

# oh-my-openagent-setup

Use this skill when the user wants to:

- set up oh-my-openagent for the first time
- reconfigure it after adding or removing providers
- fix confusing picker visibility
- refresh the expected model/config path after provider changes

This skill manages HolyCode's supported setup flow. Keep it close to upstream oh-my-openagent behavior, but apply HolyCode defaults for agent visibility and safety.

---

## Step 0 — Confirm the working context

1. Verify you are inside a HolyCode container or a HolyCode-backed OpenCode environment.
2. Use these paths as the defaults unless the user explicitly says otherwise:
   - Main OpenCode config: `~/.config/opencode/opencode.json`
   - oh-my-openagent config: `~/.config/opencode/oh-my-openagent.jsonc`
   - Skills directory: `~/.config/opencode/skills/`
3. If `opencode.json` does not exist, explain that HolyCode/OpenCode is not bootstrapped yet and stop.

---

## Step 1 — Detect current state

Before asking questions, inspect the current config state and summarize it briefly:

1. Is `oh-my-openagent` already present in the `plugin` array of `opencode.json`?
2. Does `oh-my-openagent.jsonc` already exist?
3. If it exists, extract any current values that match the questionnaire fields below.
4. If a previous backup exists, mention it but do not restore it automatically.

If the plugin-specific config already exists, this run should behave as **reconfiguration mode**.

---

## Step 2 — Ask the upstream-style questionnaire

Ask the user these questions in order. If reconfiguring, show the current value as the default.

1. Claude subscription: `yes`, `no`, or `max20`
2. OpenAI subscription: `yes` or `no`
3. Gemini availability: `yes` or `no`
4. GitHub Copilot availability: `yes` or `no`
5. OpenCode Zen availability: `yes` or `no`
6. Z.ai Coding Plan availability: `yes` or `no`
7. OpenCode Go availability: `yes` or `no`

Do not invent extra product questions unless the user explicitly asks for advanced customization.

---

## Step 3 — Apply HolyCode defaults

When writing `oh-my-openagent.jsonc`, enforce this visibility policy unless the user explicitly asks for something else:

### Visible primary agents

- `sisyphus`
- `hephaestus`
- `prometheus`
- `atlas`

### Hidden subagents

- `oracle`
- `librarian`
- `explore`
- `metis`
- `momus`
- `multimodal-looker`
- `sisyphus-junior`

Set visible agents to `mode: "all"` and subagents to `mode: "subagent"`.

---

## Step 4 — Write the configs safely

### A. Ensure plugin registration

Update `opencode.json` so the `plugin` array includes `oh-my-openagent` exactly once.

### B. Back up the existing plugin config

If `oh-my-openagent.jsonc` already exists, create a backup first:

- `oh-my-openagent.jsonc.bak`

If that name already exists, append a timestamp rather than overwriting the existing backup.

### C. Write or update `oh-my-openagent.jsonc`

The file should:

1. include the upstream schema URL if available
2. store the questionnaire answers in a clean, editable JSONC structure
3. include HolyCode's default agent visibility policy
4. preserve unrelated user fields where practical during reconfiguration

If preserving unrelated fields would be unsafe because the file is malformed, stop and explain the problem instead of blindly rewriting.

---

## Step 5 — Explain stale-model behavior honestly

Do **not** claim that HolyCode fully fixes upstream model-resolution bugs.

Instead, explain this clearly:

- Adding a provider later does not always update the visible default model automatically.
- HolyCode's supported fix path is to rerun `/oh-my-openagent-setup`, then refresh model capabilities, then verify provider/model state.
- Provider auth still belongs to OpenCode/provider login, not this skill.

---

## Step 6 — Print the follow-up commands

Always finish by showing the next actions the user may need.

### Provider auth

```bash
opencode providers list
opencode providers login
```

### Verify oh-my-openagent setup

```bash
bunx oh-my-opencode doctor
```

### Refresh model capabilities after provider changes

```bash
bunx oh-my-opencode refresh-model-capabilities
```

If the UI still shows a stale visible default after provider changes, tell the user to:

1. rerun `/oh-my-openagent-setup`
2. refresh model capabilities
3. reopen or reselect the model in the UI if needed

---

## Rules

- Keep the questionnaire close to upstream.
- Do not perform provider authentication for the user.
- Do not expose subagents in the picker by default.
- Do not overwrite an existing plugin config without making a backup first.
- Do not silently destroy malformed config files.
- Keep explanations concise and practical.
