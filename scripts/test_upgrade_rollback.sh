#!/usr/bin/env bash
set -euo pipefail

current_image="${1:?usage: scripts/test_upgrade_rollback.sh <current-image> <previous-image> [platform]}"
previous_image="${2:?usage: scripts/test_upgrade_rollback.sh <current-image> <previous-image> [platform]}"
platform="${3:-linux/amd64}"
prefix="holycode-upgrade-$$"
baseline_name="${prefix}-baseline"
upgrade_name="${prefix}-current"
rollback_name="${prefix}-rollback"
baseline_home="${prefix}-baseline-home"
baseline_workspace="${prefix}-baseline-workspace"
upgrade_home="${prefix}-upgrade-home"
upgrade_workspace="${prefix}-upgrade-workspace"

# Git for Windows may rewrite Linux paths even when MSYSTEM is not exported.
export MSYS_NO_PATHCONV=1

current_node_version="$(docker run --rm --platform "$platform" --entrypoint node "$current_image" --version)"
previous_node_version="$(docker run --rm --platform "$platform" --entrypoint node "$previous_image" --version)"
current_paperclip_version="$(docker run --rm --platform "$platform" --entrypoint node "$current_image" \
  -p 'require("/usr/local/lib/node_modules/paperclipai/package.json").version')"
previous_paperclip_version="$(docker run --rm --platform "$platform" --entrypoint node "$previous_image" \
  -p 'require("/usr/local/lib/node_modules/paperclipai/package.json").version')"

[ "$current_paperclip_version" = "2026.824.1" ]
paperclip_migration=false
if [ "$previous_paperclip_version" = "2026.707.0" ]; then
  paperclip_migration=true
elif [ "$previous_paperclip_version" = "2026.722.0" ]; then
  paperclip_migration=false
elif [ "$previous_paperclip_version" != "$current_paperclip_version" ]; then
  echo "unsupported Paperclip upgrade: $previous_paperclip_version -> $current_paperclip_version" >&2
  exit 1
fi

company_id=""
agent_id=""
legacy_acp_agent_id=""
project_id=""
issue_id=""
skill_id=""
environment_id=""
opencode_session_id="11411111-1111-4111-8111-111111111111"
legacy_acp_session_id="11422222-2222-4222-8222-222222222222"
plugin_id="11433333-3333-4333-8333-333333333333"
plugin_settings_id="11444444-4444-4444-8444-444444444444"
custom_image_template_id="11455555-5555-4555-8555-555555555555"
membership_id="11466666-6666-4666-8666-666666666666"
plugin_config_id="11477777-7777-4777-8777-777777777777"
tool_application_id="11488888-8888-4888-8888-888888888888"
tool_connection_id="11499999-9999-4999-8999-999999999999"
connection_grant_id="11500000-0000-4000-8000-000000000000"
user_id="holycode-upgrade-user"

cleanup() {
  docker rm -f "$baseline_name" "$upgrade_name" "$rollback_name" >/dev/null 2>&1 || true
  docker volume rm \
    "$baseline_home" "$baseline_workspace" \
    "$upgrade_home" "$upgrade_workspace" >/dev/null 2>&1 || true
}
trap cleanup EXIT

wait_for_services() {
  local name="$1"
  local expect_hermes="$2"

  for _ in $(seq 1 180); do
    if docker exec "$name" curl -fsS --max-time 5 -o /dev/null http://localhost:4096/ 2>/dev/null && \
       docker exec "$name" curl -fsS --max-time 5 -o /dev/null http://localhost:3100/api/health 2>/dev/null; then
      if [ "$expect_hermes" != "true" ] || docker exec "$name" curl -fsS --max-time 5 -o /dev/null \
         -H 'Authorization: Bearer holycode-upgrade-test-key' \
         http://localhost:8642/v1/models 2>/dev/null; then
        return 0
      fi
    fi
    if [ "$(docker inspect -f '{{.State.Running}}' "$name" 2>/dev/null || true)" != "true" ]; then
      docker logs "$name" || true
      return 1
    fi
    sleep 2
  done
  docker logs "$name" || true
  return 1
}

start_stack() {
  local name="$1"
  local image="$2"
  local home_volume="$3"
  local workspace_volume="$4"
  local enable_hermes="$5"

  docker run -d --platform "$platform" --name "$name" \
    -v "$home_volume:/home/opencode" \
    -v "$workspace_volume:/workspace" \
    -e PUID=2345 \
    -e PGID=2345 \
    -e ENABLE_PAPERCLIP=true \
    -e ENABLE_HERMES="$enable_hermes" \
    -e PAPERCLIP_DEPLOYMENT_MODE=local_trusted \
    -e PAPERCLIP_BIND=loopback \
    -e API_SERVER_KEY=holycode-upgrade-test-key \
    -e CLIPROXYAPI_ENABLED=true \
    -e CLIPROXYAPI_MODEL=holycode-upgrade-model \
    -e CLIPROXYAPI_API_KEY=holycode-upgrade-provider-key \
    "$image" >/dev/null
  wait_for_services "$name" "$enable_hermes"
}

initialize_openspec_fixture() {
  local workspace_volume="$1"

  docker run --rm --platform "$platform" --network none --entrypoint sh \
    --user 0:0 \
    -v "$workspace_volume:/workspace" \
    "$current_image" -lc '
      chown 2345:2345 /workspace
      chmod 0755 /workspace
      install -o 2345 -g 2345 -m 0644 /dev/null /workspace/.holycode-openspec-fixture
    '
  docker run --rm --platform "$platform" --network none --entrypoint sh \
    --user 2345:2345 \
    -e OPENSPEC_TELEMETRY=0 \
    -v "$workspace_volume:/workspace" \
    -w /workspace \
    "$current_image" -lc '
      if ! test -w /workspace; then
        stat -c "%A %u:%g %n" /workspace >&2
        echo "OpenSpec fixture is not writable by 2345:2345" >&2
        exit 1
      fi
      openspec init --tools opencode >/dev/null
    '
  docker run --rm --platform "$platform" --network none --entrypoint sh \
    --user 0:0 \
    -v "$workspace_volume:/workspace" \
    "$current_image" -lc '
      rm -f /workspace/.holycode-openspec-fixture
      chown 2345:2345 /workspace
      chmod 0755 /workspace
    '
}

snapshot_openspec_volume() {
  local workspace_volume="$1"

  docker run --rm --platform "$platform" --network none --entrypoint sh \
    -v "$workspace_volume:/workspace:ro" \
    "$current_image" -lc '
      {
        find /workspace -xdev -printf "%P|%y|%m|%U:%G\n" | LC_ALL=C sort
        find /workspace -xdev -type l -printf "%P|%l\n" | LC_ALL=C sort
        find /workspace -xdev -type f -print0 | LC_ALL=C sort -z | xargs -0r sha256sum
      } | sha256sum
    '
}

clone_volume() {
  local source_volume="$1"
  local target_volume="$2"

  docker volume create "$target_volume" >/dev/null
  docker run --rm --platform "$platform" --entrypoint sh \
    -v "$source_volume:/from:ro" \
    -v "$target_volume:/to" \
    "$current_image" -lc 'cp -a /from/. /to/'
}

api_get() {
  local name="$1"
  local path="$2"

  docker exec "$name" curl -fsS "http://localhost:3100${path}"
}

api_post() {
  local name="$1"
  local path="$2"
  local body="$3"

  printf '%s' "$body" | docker exec -i "$name" curl -fsS \
    -H 'Content-Type: application/json' \
    --data-binary '@-' \
    "http://localhost:3100${path}"
}

json_field() {
  local name="$1"
  local field="$2"

  docker exec -i "$name" python3 -c '
import json
import sys

value = json.load(sys.stdin)
for part in sys.argv[1].split("."):
    value = value[part]
print(value)
' "$field"
}

assert_json_field() {
  local name="$1"
  local field="$2"
  local expected="$3"

  docker exec -i "$name" python3 -c '
import json
import sys

value = json.load(sys.stdin)
for part in sys.argv[1].split("."):
    value = value[part]
actual = str(value)
expected = sys.argv[2]
if actual != expected:
    raise SystemExit(f"{sys.argv[1]}: expected {expected!r}, got {actual!r}")
' "$field" "$expected"
}

seed_internal_paperclip_state() {
  local name="$1"

  docker exec -i "$name" node --input-type=module - \
    "$company_id" \
    "$agent_id" \
    "$legacy_acp_agent_id" \
    "$environment_id" \
    "$opencode_session_id" \
    "$legacy_acp_session_id" \
    "$plugin_id" \
    "$plugin_settings_id" \
    "$custom_image_template_id" \
    "$membership_id" \
    "$plugin_config_id" \
    "$user_id" <<'NODE'
import postgres from "/usr/local/lib/node_modules/paperclipai/node_modules/postgres/src/index.js";

const [
  companyId,
  agentId,
  legacyAcpAgentId,
  environmentId,
  opencodeSessionId,
  legacyAcpSessionId,
  pluginId,
  pluginSettingsId,
  customImageTemplateId,
  membershipId,
  pluginConfigId,
  userId,
] = process.argv.slice(2);

const sql = postgres({
  host: "127.0.0.1",
  port: 54329,
  database: "paperclip",
  username: "paperclip",
  password: "paperclip",
});

await sql`
  insert into "user" (
    id, name, email, email_verified, created_at, updated_at
  ) values (
    ${userId},
    'Upgrade User',
    'upgrade-user@holycode.invalid',
    true,
    now(),
    now()
  )
`;

await sql`
  insert into company_memberships (
    id, company_id, principal_type, principal_id, status, membership_role
  ) values (
    ${membershipId}::uuid,
    ${companyId}::uuid,
    'user',
    ${userId},
    'active',
    'owner'
  )
`;

await sql`
  insert into agent_task_sessions (
    id, company_id, agent_id, adapter_type, task_key,
    session_params_json, session_display_id
  ) values (
    ${opencodeSessionId}::uuid,
    ${companyId}::uuid,
    ${agentId}::uuid,
    'opencode_local',
    'holycode-upgrade-opencode',
    '{"fixture":"preserve"}'::jsonb,
    'holycode-upgrade-opencode'
  )
`;

await sql`
  insert into agent_task_sessions (
    id, company_id, agent_id, adapter_type, task_key,
    session_params_json, session_display_id
  ) values (
    ${legacyAcpSessionId}::uuid,
    ${companyId}::uuid,
    ${legacyAcpAgentId}::uuid,
    'acpx_local',
    'holycode-upgrade-acpx',
    '{"fixture":"delete-during-0136"}'::jsonb,
    'holycode-upgrade-acpx'
  )
`;

await sql`
  insert into agent_runtime_state (
    agent_id, company_id, adapter_type, session_id, state_json, last_error
  ) values (
    ${legacyAcpAgentId}::uuid,
    ${companyId}::uuid,
    'acpx_local',
    'holycode-legacy-runtime-session',
    '{"fixture":"reset-during-0136"}'::jsonb,
    'holycode legacy runtime error'
  )
`;

await sql`
  insert into plugins (
    id, plugin_key, package_name, version, categories, manifest_json, status
  ) values (
    ${pluginId}::uuid,
    'holycode-upgrade-fixture',
    '@holycode/upgrade-fixture',
    '1.0.0',
    '["validation"]'::jsonb,
    '{"id":"holycode-upgrade-fixture","name":"HolyCode Upgrade Fixture"}'::jsonb,
    'installed'
  )
`;

await sql`
  insert into plugin_config (
    id, plugin_id, config_json, last_error
  ) values (
    ${pluginConfigId}::uuid,
    ${pluginId}::uuid,
    '{"fixture":"company-scope"}'::jsonb,
    null
  )
`;

await sql`
  insert into plugin_company_settings (
    id, company_id, plugin_id, settings_json, enabled
  ) values (
    ${pluginSettingsId}::uuid,
    ${companyId}::uuid,
    ${pluginId}::uuid,
    '{"fixture":"owned-by-company"}'::jsonb,
    true
  )
`;

await sql`
  insert into environment_custom_image_templates (
    id, environment_id, provider, template_kind, template_ref,
    status, created_by_agent_id, metadata
  ) values (
    ${customImageTemplateId}::uuid,
    ${environmentId}::uuid,
    'fixture',
    'container',
    'holycode/upgrade-fixture:baseline',
    'active',
    ${agentId}::uuid,
    '{"fixture":"v1.1.3"}'::jsonb
  )
`;

await sql.end();
NODE
}

seed_post_upgrade_connections() {
  local name="$1"

  docker exec -i "$name" node --input-type=module - \
    "$company_id" \
    "$agent_id" \
    "$tool_application_id" \
    "$tool_connection_id" \
    "$connection_grant_id" \
    "$user_id" <<'NODE'
import postgres from "/usr/local/lib/node_modules/paperclipai/node_modules/postgres/src/index.js";

const [
  companyId,
  agentId,
  applicationId,
  connectionId,
  grantId,
  userId,
] = process.argv.slice(2);
const sql = postgres({
  host: "127.0.0.1",
  port: 54329,
  database: "paperclip",
  username: "paperclip",
  password: "paperclip",
});

await sql`
  insert into tool_applications (
    id, company_id, name, type, status, metadata, application_key,
    description, owner_user_id
  ) values (
    ${applicationId}::uuid,
    ${companyId}::uuid,
    'HolyCode Upgrade MCP',
    'mcp',
    'active',
    '{"fixture":"post-migration"}'::jsonb,
    'holycode-upgrade-mcp',
    'Connection persistence fixture',
    ${userId}
  )
`;

await sql`
  insert into tool_connections (
    id, company_id, application_id, name, transport, status, enabled,
    config, credential_refs, connection_kind, transport_config,
    credential_secret_refs, uid, ownership, auth_kind, created_by_agent_id,
    created_by_user_id
  ) values (
    ${connectionId}::uuid,
    ${companyId}::uuid,
    ${applicationId}::uuid,
    'HolyCode Upgrade Connection',
    'mcp_remote',
    'active',
    true,
    '{"url":"https://mcp.holycode.invalid"}'::jsonb,
    '[]'::jsonb,
    'managed',
    '{"url":"https://mcp.holycode.invalid"}'::jsonb,
    '[]'::jsonb,
    'holycode-upgrade-mcp/connection',
    'customer',
    'none',
    ${agentId}::uuid,
    ${userId}
  )
`;

await sql`
  insert into connection_grants (
    id, company_id, connection_id, kind, credential_secret_refs,
    status, is_default, created_by_agent_id, created_by_user_id
  ) values (
    ${grantId}::uuid,
    ${companyId}::uuid,
    ${connectionId}::uuid,
    'workspace',
    '[]'::jsonb,
    'active',
    true,
    ${agentId}::uuid,
    ${userId}
  )
`;

await sql.end();
NODE
}

assert_post_upgrade_connections() {
  local name="$1"

  docker exec -i "$name" node --input-type=module - \
    "$company_id" \
    "$tool_application_id" \
    "$tool_connection_id" \
    "$connection_grant_id" \
    "$user_id" <<'NODE'
import postgres from "/usr/local/lib/node_modules/paperclipai/node_modules/postgres/src/index.js";

const [companyId, applicationId, connectionId, grantId, userId] =
  process.argv.slice(2);
const sql = postgres({
  host: "127.0.0.1",
  port: 54329,
  database: "paperclip",
  username: "paperclip",
  password: "paperclip",
});

const rows = await sql`
  select
    a.application_key,
    a.owner_user_id,
    c.uid,
    c.transport,
    c.ownership,
    c.auth_kind,
    g.kind,
    g.status,
    g.is_default,
    g.created_by_user_id
  from tool_applications a
  join tool_connections c
    on c.application_id = a.id and c.company_id = a.company_id
  join connection_grants g
    on g.connection_id = c.id and g.company_id = c.company_id
  where a.id = ${applicationId}::uuid
    and c.id = ${connectionId}::uuid
    and g.id = ${grantId}::uuid
    and a.company_id = ${companyId}::uuid
`;
if (rows.length !== 1) throw new Error(`connection fixture count: ${rows.length}`);
const row = rows[0];
if (
  row.application_key !== "holycode-upgrade-mcp" ||
  row.owner_user_id !== userId ||
  row.uid !== "holycode-upgrade-mcp/connection" ||
  row.transport !== "mcp_remote" ||
  row.ownership !== "customer" ||
  row.auth_kind !== "none" ||
  row.kind !== "workspace" ||
  row.status !== "active" ||
  row.is_default !== true ||
  row.created_by_user_id !== userId
) {
  throw new Error(`unexpected connection fixture: ${JSON.stringify(row)}`);
}

await sql.end();
NODE
}

seed_paperclip_state() {
  local name="$1"
  local response

  response="$(api_post "$name" "/api/companies" \
    '{"name":"HolyCode Upgrade Fixture","description":"Paperclip v1.1.4 migration state","budgetMonthlyCents":12345}')"
  company_id="$(printf '%s' "$response" | json_field "$name" id)"

  response="$(api_post "$name" "/api/companies/${company_id}/agents" \
    '{"name":"Upgrade CEO","role":"ceo","adapterType":"opencode_local","adapterConfig":{"cwd":"/workspace","model":"holycode/upgrade-model"},"budgetMonthlyCents":5000,"metadata":{"fixture":"v1.1.3"}}')"
  agent_id="$(printf '%s' "$response" | json_field "$name" id)"

  response="$(api_post "$name" "/api/companies/${company_id}/agents" \
    '{"name":"Legacy ACP Agent","role":"engineer","adapterType":"acpx_local","adapterConfig":{"agent":"codex","cwd":"/workspace","model":"openai/gpt-5","reasoningEffort":"high"},"metadata":{"fixture":"acpx-migration"}}')"
  legacy_acp_agent_id="$(printf '%s' "$response" | json_field "$name" id)"

  response="$(api_post "$name" "/api/companies/${company_id}/projects" \
    "{\"name\":\"Upgrade Project\",\"description\":\"Persisted project fixture\",\"status\":\"in_progress\",\"leadAgentId\":\"${agent_id}\",\"workspace\":{\"name\":\"Primary\",\"sourceType\":\"local_path\",\"cwd\":\"/workspace\",\"isPrimary\":true}}")"
  project_id="$(printf '%s' "$response" | json_field "$name" id)"

  response="$(api_post "$name" "/api/companies/${company_id}/issues" \
    "{\"projectId\":\"${project_id}\",\"title\":\"Persist migration state\",\"description\":\"Upgrade fixture issue\",\"status\":\"todo\",\"priority\":\"high\",\"assigneeAgentId\":\"${agent_id}\"}")"
  issue_id="$(printf '%s' "$response" | json_field "$name" id)"

  response="$(api_post "$name" "/api/companies/${company_id}/skills" \
    '{"name":"Upgrade Verification","slug":"upgrade-verification","description":"Persisted skill fixture","markdown":"# Upgrade Verification\n\nConfirm Paperclip state survives.","categories":["testing"],"sharingScope":"company"}')"
  skill_id="$(printf '%s' "$response" | json_field "$name" id)"

  response="$(api_get "$name" "/api/companies/${company_id}/environments")"
  environment_id="$(printf '%s' "$response" | docker exec -i "$name" python3 -c '
import json
import sys

environments = json.load(sys.stdin)
local = next(item for item in environments if item["driver"] == "local")
print(local["id"])
')"

  if [ "$paperclip_migration" = "true" ]; then
    seed_internal_paperclip_state "$name"
  fi
}

assert_internal_paperclip_state() {
  local name="$1"
  local phase="$2"

  docker exec -i "$name" node --input-type=module - \
    "$phase" \
    "$company_id" \
    "$agent_id" \
    "$legacy_acp_agent_id" \
    "$environment_id" \
    "$opencode_session_id" \
    "$legacy_acp_session_id" \
    "$plugin_id" \
    "$plugin_settings_id" \
    "$custom_image_template_id" \
    "$membership_id" \
    "$plugin_config_id" \
    "$user_id" <<'NODE'
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import postgres from "/usr/local/lib/node_modules/paperclipai/node_modules/postgres/src/index.js";

const [
  phase,
  companyId,
  agentId,
  legacyAcpAgentId,
  environmentId,
  opencodeSessionId,
  legacyAcpSessionId,
  pluginId,
  pluginSettingsId,
  customImageTemplateId,
  membershipId,
  pluginConfigId,
  userId,
] = process.argv.slice(2);

const sql = postgres({
  host: "127.0.0.1",
  port: 54329,
  database: "paperclip",
  username: "paperclip",
  password: "paperclip",
});

const requireCount = async (label, query, expected = 1) => {
  const rows = await query;
  const actual = Number(rows[0]?.count ?? 0);
  if (actual !== expected) {
    throw new Error(`${label}: expected ${expected}, got ${actual}`);
  }
};

await requireCount(
  "user",
  sql`select count(*) from "user" where id = ${userId} and email = 'upgrade-user@holycode.invalid'`,
);
await requireCount(
  "company membership",
  sql`
    select count(*)
    from company_memberships
    where id = ${membershipId}::uuid
      and company_id = ${companyId}::uuid
      and principal_type = 'user'
      and principal_id = ${userId}
      and membership_role = 'owner'
  `,
);
await requireCount(
  "OpenCode task session",
  sql`select count(*) from agent_task_sessions where id = ${opencodeSessionId}::uuid`,
);
await requireCount(
  "plugin",
  sql`select count(*) from plugins where id = ${pluginId}::uuid and plugin_key = 'holycode-upgrade-fixture'`,
);
await requireCount(
  "plugin company settings",
  sql`select count(*) from plugin_company_settings where id = ${pluginSettingsId}::uuid and company_id = ${companyId}::uuid and enabled = true`,
);
await requireCount(
  "custom image template",
  sql`select count(*) from environment_custom_image_templates where id = ${customImageTemplateId}::uuid and environment_id = ${environmentId}::uuid and template_ref = 'holycode/upgrade-fixture:baseline'`,
);

if (phase === "baseline") {
  await requireCount(
    "legacy ACP task session before migration",
    sql`select count(*) from agent_task_sessions where id = ${legacyAcpSessionId}::uuid`,
  );
  await requireCount(
    "legacy ACP agent before migration",
    sql`select count(*) from agents where id = ${legacyAcpAgentId}::uuid and adapter_type = 'acpx_local'`,
  );
  await requireCount(
    "legacy ACP runtime state before migration",
    sql`
      select count(*)
      from agent_runtime_state
      where agent_id = ${legacyAcpAgentId}::uuid
        and adapter_type = 'acpx_local'
        and session_id = 'holycode-legacy-runtime-session'
        and state_json ->> 'fixture' = 'reset-during-0136'
        and last_error = 'holycode legacy runtime error'
    `,
  );
  await requireCount(
    "plugin config before company scoping",
    sql`
      select count(*)
      from plugin_config
      where id = ${pluginConfigId}::uuid
        and plugin_id = ${pluginId}::uuid
        and config_json ->> 'fixture' = 'company-scope'
    `,
  );
} else {
  await requireCount(
    "legacy ACP task session removed by migration 0136",
    sql`select count(*) from agent_task_sessions where id = ${legacyAcpSessionId}::uuid`,
    0,
  );
  await requireCount(
    "legacy ACP agent converted by migration 0136",
    sql`
      select count(*)
      from agents
      where id = ${legacyAcpAgentId}::uuid
        and adapter_type = 'codex_local'
        and adapter_config ->> 'engine' = 'acp'
        and adapter_config ->> 'modelReasoningEffort' = 'high'
        and not (adapter_config ? 'agent')
        and not (adapter_config ? 'reasoningEffort')
    `,
  );
  await requireCount(
    "legacy ACP runtime state reset by migration 0136",
    sql`
      select count(*)
      from agent_runtime_state
      where agent_id = ${legacyAcpAgentId}::uuid
        and company_id = ${companyId}::uuid
        and adapter_type = 'codex_local'
        and session_id is null
        and state_json = '{}'::jsonb
        and last_error is null
    `,
  );
  await requireCount(
    "plugin config scoped by migration 0164",
    sql`
      select count(*)
      from plugin_config
      where id = ${pluginConfigId}::uuid
        and plugin_id = ${pluginId}::uuid
        and company_id = ${companyId}::uuid
        and config_json ->> 'fixture' = 'company-scope'
    `,
  );
  await requireCount(
    "connections v3 table",
    sql`
      select count(*)
      from information_schema.tables
      where table_schema = 'public' and table_name = 'connection_grants'
    `,
  );

  const migrationDir =
    "/usr/local/lib/node_modules/paperclipai/node_modules/@paperclipai/db/dist/migrations";
  for (const filename of [
    "0136_acpx_default_engine_migration.sql",
    "0164_plugin_config_company_scope.sql",
    "0182_connections_v3_schema_core.sql",
    "0183_connection_user_authorization_state.sql",
  ]) {
    const hash = createHash("sha256")
      .update(readFileSync(`${migrationDir}/${filename}`))
      .digest("hex");
    await requireCount(
      `migration journal ${filename}`,
      sql`select count(*) from drizzle.__drizzle_migrations where hash = ${hash}`,
    );
  }
}

await sql.end();
NODE
}

assert_persisted_state() {
  local name="$1"
  local phase="$2"

  docker exec "$name" test -f /home/opencode/.claude/holycode-upgrade-auth-marker
  docker exec "$name" test -f /home/opencode/.hermes/holycode-upgrade-marker
  docker exec "$name" test -f /home/opencode/.paperclip/instances/default/data/holycode-upgrade-marker
  docker exec "$name" test -f /workspace/holycode-upgrade-marker
  docker exec "$name" grep -Fq 'holycode-upgrade-model' /home/opencode/.config/opencode/opencode.json
  [ "$(docker exec "$name" stat -c %u /workspace/holycode-upgrade-marker)" = "2345" ]

  api_get "$name" "/api/companies/${company_id}" |
    assert_json_field "$name" name "HolyCode Upgrade Fixture"
  api_get "$name" "/api/agents/${agent_id}" |
    assert_json_field "$name" adapterConfig.model "holycode/upgrade-model"
  api_get "$name" "/api/projects/${project_id}" |
    assert_json_field "$name" primaryWorkspace.cwd "/workspace"
  api_get "$name" "/api/issues/${issue_id}" |
    assert_json_field "$name" projectId "$project_id"
  api_get "$name" "/api/companies/${company_id}/skills/${skill_id}" |
    assert_json_field "$name" slug "upgrade-verification"

  if [ "$paperclip_migration" = "true" ]; then
    assert_internal_paperclip_state "$name" "$phase"
  fi
}

docker pull --platform "$platform" "$previous_image" >/dev/null
docker volume create "$baseline_home" >/dev/null
docker volume create "$baseline_workspace" >/dev/null

initialize_openspec_fixture "$baseline_workspace"
start_stack "$baseline_name" "$previous_image" "$baseline_home" "$baseline_workspace" false
seed_paperclip_state "$baseline_name"
docker exec -u opencode "$baseline_name" sh -lc '
  mkdir -p /home/opencode/.claude /home/opencode/.hermes
  touch /home/opencode/.claude/holycode-upgrade-auth-marker
  touch /home/opencode/.hermes/holycode-upgrade-marker
  touch /home/opencode/.paperclip/instances/default/data/holycode-upgrade-marker
  touch /workspace/holycode-upgrade-marker
'
assert_persisted_state "$baseline_name" baseline
openspec_before="$(snapshot_openspec_volume "$baseline_workspace")"
docker rm -f "$baseline_name" >/dev/null

clone_volume "$baseline_home" "$upgrade_home"
clone_volume "$baseline_workspace" "$upgrade_workspace"

start_stack "$upgrade_name" "$current_image" "$upgrade_home" "$upgrade_workspace" false
openspec_after="$(snapshot_openspec_volume "$upgrade_workspace")"
[ "$openspec_before" = "$openspec_after" ]
openspec_startup_no_mutation=true
assert_persisted_state "$upgrade_name" upgraded
if [ "$paperclip_migration" = "true" ]; then
  seed_post_upgrade_connections "$upgrade_name"
  assert_post_upgrade_connections "$upgrade_name"
  upgrade_logs="$(docker logs "$upgrade_name" 2>&1)"
  grep -Fq '0136_acpx_default_engine_migration.sql' <<<"$upgrade_logs"
  grep -Fq '0183_connection_user_authorization_state.sql' <<<"$upgrade_logs"
fi
docker exec "$upgrade_name" node --version | grep -Fx "$current_node_version"
docker restart "$upgrade_name" >/dev/null
wait_for_services "$upgrade_name" false
openspec_after="$(snapshot_openspec_volume "$upgrade_workspace")"
[ "$openspec_before" = "$openspec_after" ]
test "$openspec_startup_no_mutation" = true
assert_persisted_state "$upgrade_name" upgraded
if [ "$paperclip_migration" = "true" ]; then
  assert_post_upgrade_connections "$upgrade_name"
fi
docker rm -f "$upgrade_name" >/dev/null

start_stack "$rollback_name" "$previous_image" "$baseline_home" "$baseline_workspace" false
assert_persisted_state "$rollback_name" baseline
docker exec "$rollback_name" node --version | grep -Fx "$previous_node_version"

echo "upgrade and rollback validation passed for $platform"
