import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReleaseContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        cls.entrypoint = (ROOT / "scripts" / "entrypoint.sh").read_text(encoding="utf-8")
        cls.smoke = (ROOT / "scripts" / "smoke_image.sh").read_text(encoding="utf-8")
        cls.claude_auth = (ROOT / "scripts" / "test_claude_auth.sh").read_text(encoding="utf-8")
        cls.upgrade = (ROOT / "scripts" / "test_upgrade_rollback.sh").read_text(
            encoding="utf-8"
        )
        cls.publish = (ROOT / ".github" / "workflows" / "docker-publish.yml").read_text(encoding="utf-8")
        cls.protected = cls.publish
        cls.pr_validation = (ROOT / ".github" / "workflows" / "pr-validation.yml").read_text(encoding="utf-8")
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.dockerhub = (ROOT / "docs" / "dockerhub-description.md").read_text(encoding="utf-8")
        cls.gitattributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        cls.python_lock = (ROOT / "config" / "python-requirements.lock").read_text(encoding="utf-8")
        cls.python_seed_lock = (
            ROOT / "config" / "python-seed-requirements.lock"
        ).read_text(encoding="utf-8")
        cls.renovate = json.loads((ROOT / "renovate.json").read_text(encoding="utf-8"))

    def test_executable_scripts_use_lf_shebangs(self):
        scripts = [
            ROOT / "scripts" / "validate_npm_script_policy.py",
            ROOT / "scripts" / "validate_chromium_seccomp.py",
            ROOT / "scripts" / "entrypoint.sh",
            ROOT / "scripts" / "bootstrap.sh",
            ROOT / "scripts" / "smoke_image.sh",
            ROOT / "scripts" / "test_claude_auth.sh",
            ROOT / "scripts" / "test_plugin_modes.sh",
            ROOT / "scripts" / "test_upgrade_rollback.sh",
            ROOT / "scripts" / "validate_renovate_extraction.sh",
            ROOT / "scripts" / "validate_scanner_findings.py",
        ]

        for script in scripts:
            with self.subTest(script=script.name):
                first_line = script.read_bytes().splitlines(keepends=True)[0]
                self.assertNotIn(b"\r\n", first_line)

    def test_release_dependency_pins(self):
        expected = (
            "ARG S6_OVERLAY_VERSION=3.2.3.2",
            "ARG FZF_VERSION=0.74.1",
            "ARG OPENCODE_VERSION=1.18.9",
            "ARG CLAUDE_CODE_VERSION=2.1.220",
            "ARG PAPERCLIP_VERSION=2026.722.0",
            "ARG NPM_VERSION=12.0.2",
            "ARG NPM_BRACE_EXPANSION_VERSION=5.0.8",
            "ARG NPM_TAR_VERSION=7.5.22",
            "ARG PIP_VENDOR_MSGPACK_VERSION=1.2.1",
            "ARG PIP_VENDOR_PKG_RESOURCES_VERSION=80.9.0",
            "ARG PNPM_VERSION=11.18.0",
            "ARG VITE_VERSION=8.1.5",
            "ARG PRETTIER_VERSION=3.9.6",
            "ARG PRISMA_VERSION=7.9.1",
            "ARG LIGHTHOUSE_VERSION=13.4.1",
            "ARG WRANGLER_VERSION=4.115.0",
            "requests==2.34.2",
            "pillow==12.3.0",
            "postgresql-client-17 redis-tools sqlite3",
            "matplotlib==3.11.1",
            "pandas==3.0.5",
            "tqdm==4.70.0",
            "fastapi==0.141.1",
            "uvicorn==0.52.0",
            "packaging==26.2",
            "wheel==0.47.0",
            "rich==15.0.0",
        )
        for value in expected:
            with self.subTest(value=value):
                source = self.python_lock if "==" in value else self.dockerfile
                self.assertIn(value, source)
        self.assertNotIn("postgresql-client redis-tools sqlite3", self.dockerfile)
        self.assertIn(
            "04c721c2c7448767e9e3f2520a475663d8ee0f09c31890f6d2bd70fd636a9647",
            self.dockerfile,
        )
        self.assertIn(
            "f36b47402ecde768dbfafc46e8e4207b4360c654f1f3bb84475f0a28628fb19c",
            self.dockerfile,
        )
        self.assertIn("bom.cdx.json", self.dockerfile)
        self.assertIn("msgpack==${PIP_VENDOR_MSGPACK_VERSION}", self.dockerfile)
        self.assertIn(
            "setuptools==${PIP_VENDOR_PKG_RESOURCES_VERSION}",
            self.dockerfile,
        )
        self.assertIn(
            "node -e 'const ssh2=require("
            '"/usr/local/lib/node_modules/paperclipai/node_modules/ssh2"'
            "); if(typeof ssh2.Client!==\"function\") process.exit(1)' && \\\n"
            "    rm -rf /root/.npm",
            self.dockerfile,
        )
        self.assertIn("test ! -e /root/.npm", self.smoke)

    def test_each_root_npm_layer_removes_its_cache(self):
        run_instructions = []
        current = []
        for line in self.dockerfile.splitlines():
            if current:
                current.append(line)
                if not line.rstrip().endswith("\\"):
                    run_instructions.append("\n".join(current))
                    current = []
            elif line.startswith("RUN "):
                current = [line]
                if not line.rstrip().endswith("\\"):
                    run_instructions.append(line)
                    current = []

        npm_commands = re.compile(r"\bnpm (?:i|install|view|pack|ls)\b")
        npm_layers = [instruction for instruction in run_instructions if npm_commands.search(instruction)]
        self.assertTrue(npm_layers)
        for instruction in npm_layers:
            with self.subTest(instruction=instruction.splitlines()[0]):
                self.assertIn("rm -rf /root/.npm", instruction)

    def test_github_cli_is_rebuilt_with_fixed_go_toolchain(self):
        self.assertIn(
            "FROM --platform=$BUILDPLATFORM golang:1.26.5-trixie@sha256:"
            "4ee9ffa999b4583ce281939cdff828763083610292f252279a0cee77473bd9a7 "
            "AS github-cli-builder",
            self.dockerfile,
        )
        self.assertIn("ARG GITHUB_CLI_VERSION=2.96.0", self.dockerfile)
        self.assertIn(
            "ARG GITHUB_CLI_REF=b300f2ec7ec9dc9addc39b2ad88c54097ded7ca0",
            self.dockerfile,
        )
        self.assertIn('test "$(git rev-parse HEAD)" = "${GITHUB_CLI_REF}"', self.dockerfile)
        self.assertIn('go version -m /out/gh | grep -F "go1.26.5"', self.dockerfile)
        self.assertIn(
            "go version -m /out/gh | grep -E "
            "'github.com/klauspost/compress[[:space:]]+v1\\.18\\.7'",
            self.dockerfile,
        )
        self.assertIn(
            "go version -m /out/gh | grep -E "
            "'golang.org/x/text[[:space:]]+v0\\.39\\.0'",
            self.dockerfile,
        )
        self.assertIn("COPY --from=github-cli-builder /out/gh /usr/local/bin/gh", self.dockerfile)
        self.assertNotIn("https://cli.github.com/packages", self.dockerfile)
        self.assertIn("expected_github_cli", self.smoke)
        self.assertIn('test "$(command -v gh)" = "/usr/local/bin/gh"', self.smoke)
        self.assertIn('gh version $EXPECTED_GITHUB_CLI', self.smoke)
        self.assertIn("! dpkg-query -W gh", self.smoke)

    def test_fzf_and_lazygit_are_rebuilt_from_exact_release_sources(self):
        self.assertIn(
            "ARG FZF_REF=eae8d9d27eaeffc777699c01bf8f8b8c071908c1",
            self.dockerfile,
        )
        self.assertIn(
            "ARG LAZYGIT_REF=aafe61082e7ed383d318fd40e48f85645e6afc7b",
            self.dockerfile,
        )
        self.assertIn(
            "go version -m /out/fzf | grep -E "
            "'golang.org/x/sys[[:space:]]+v0\\.44\\.0'",
            self.dockerfile,
        )
        self.assertIn(
            "go version -m /out/lazygit | grep -E "
            "'golang.org/x/text[[:space:]]+v0\\.39\\.0'",
            self.dockerfile,
        )
        self.assertIn(
            'LAZYGIT_MODULE_FILES_SHA256="$(sha256sum go.mod go.sum)"',
            self.dockerfile,
        )
        self.assertIn(
            'test "$(sha256sum go.mod go.sum)" = "${LAZYGIT_MODULE_FILES_SHA256}"',
            self.dockerfile,
        )
        self.assertNotIn("git diff --exit-code -- go.mod go.sum", self.dockerfile)
        self.assertIn("COPY --from=fzf-builder /out/fzf /usr/local/bin/fzf", self.dockerfile)
        self.assertIn(
            "COPY --from=lazygit-builder /out/lazygit /usr/local/bin/lazygit",
            self.dockerfile,
        )

    def test_vulnerable_bundled_tools_are_removed(self):
        for value in (
            "HERMES_AGENT_VERSION",
            "HERMES_AGENT_REF",
            "io.holycode.version.hermes",
            "VERCEL_VERSION",
            "io.holycode.version.vercel",
            '"vercel@',
            "concurrently@",
            "@lhci/cli@",
            "sharp-cli@",
            "NETLIFY_CLI_VERSION",
            "io.holycode.version.netlify-cli",
            '"netlify-cli@',
            "serve@",
        ):
            with self.subTest(value=value):
                self.assertNotIn(value, self.dockerfile)

        for command in ("vercel", "concurrently", "lhci", "sharp", "netlify", "serve"):
            with self.subTest(command=command):
                self.assertIn(f"! command -v {command}", self.smoke)

    def test_scanner_remediations_are_pinned(self):
        self.assertIn("ARG PIP_VERSION=26.2", self.dockerfile)
        self.assertIn("ARG PIP_VENDOR_MSGPACK_VERSION=1.2.1", self.dockerfile)
        self.assertIn(
            "ARG PIP_VENDOR_MSGPACK_SHA256="
            "04c721c2c7448767e9e3f2520a475663d8ee0f09c31890f6d2bd70fd636a9647",
            self.dockerfile,
        )
        self.assertIn("ARG PIP_VENDOR_PKG_RESOURCES_VERSION=80.9.0", self.dockerfile)
        self.assertIn(
            "ARG PIP_VENDOR_PKG_RESOURCES_SHA256="
            "f36b47402ecde768dbfafc46e8e4207b4360c654f1f3bb84475f0a28628fb19c",
            self.dockerfile,
        )
        self.assertIn(
            "COPY patches/pip-vendored-pkg-resources-80.9.0.patch",
            self.dockerfile,
        )
        self.assertIn("bom.cdx.json", self.dockerfile)
        self.assertIn("ARG PAPERCLIP_UNDICI_VERSION=6.28.0", self.dockerfile)
        self.assertIn("ARG NPM_TAR_VERSION=7.5.22", self.dockerfile)
        self.assertIn("python3-pip python3-wheel", self.dockerfile)
        self.assertIn(
            "--require-hashes -r /usr/local/share/holycode/python-seed-requirements.lock",
            self.dockerfile,
        )
        for package in ("pip==26.2", "setuptools==83.0.0", "packaging==26.2", "wheel==0.47.0"):
            with self.subTest(package=package):
                self.assertIn(package, self.python_seed_lock)
        self.assertIn("undici@${PAPERCLIP_UNDICI_VERSION}", self.dockerfile)
        self.assertIn(
            "sha512-LIY910g9TI13YS95lrMFrs8Rm/u/irgHeTWoKCoteeJ04CUJ92eEfj0rVn+7VKMPBpUPiUoBKfhNyLI23EE/KA==",
            self.dockerfile,
        )
        self.assertIn(
            'grep -F "<policy domain=\\"coder\\" rights=\\"read|write\\" '
            'pattern=\\"{GIF,JPEG,PNG,WEBP}\\" />"',
            self.smoke,
        )
        self.assertIn("npm ls undici --all", self.dockerfile)
        self.assertIn("npm ls tar --all", self.dockerfile)
        self.assertIn("expected_npm_tar", self.smoke)
        self.assertIn("cursor_cloud_api_key_missing", self.smoke)

    def test_claude_auth_is_installed_from_verified_offline_payload(self):
        self.assertIn("ARG CLAUDE_AUTH_PLUGIN_VERSION=2.1.5", self.dockerfile)
        self.assertIn(
            "sha512-rRZ3aZJEbgHsXzox1vkXY3sIrE3Z6c5ya/hEJJb2/XavuPufvTLI9dN2VHfvhFTl"
            "6eZPbs10hlSirfGnyLr46Q==",
            self.dockerfile,
        )
        self.assertIn('dist.integrity)" =', self.dockerfile)
        self.assertIn("npm pack --silent --pack-destination /tmp", self.dockerfile)
        self.assertIn("/usr/local/share/holycode/plugins/opencode-claude-auth", self.dockerfile)
        self.assertIn('CLAUDE_AUTH_PLUGIN_VERSION="2.1.5"', self.entrypoint)
        self.assertIn("install_offline_claude_auth", self.entrypoint)
        self.assertNotIn('opencode plugin "$plugin_spec" -g -f', self.entrypoint)
        self.assertIn("claude auth status --json", self.smoke)
        self.assertIn(
            '.loggedIn == false and .authMethod == \\"none\\"',
            self.smoke,
        )

    def test_oh_my_openagent_managed_install_is_suspended(self):
        self.assertNotIn("OH_MY_OPENAGENT_PLUGIN_VERSION", self.entrypoint)
        self.assertNotIn("ensure_plugin_installed \"$OH_MY_OPENAGENT_PLUGIN_NAME\"", self.entrypoint)
        self.assertNotIn("plugin_spec_from_config", self.entrypoint)
        self.assertIn(
            'migrate_oh_my_openagent_config "$CONFIG_FILE"',
            self.entrypoint,
        )
        self.assertIn("HolyCode-managed oh-my-openagent installation is unavailable", self.entrypoint)
        self.assertIn("existing configuration and data were not changed", self.entrypoint)
        self.assertIn(
            ".holycode-oh-my-openagent-migrated-v1.1.4",
            self.entrypoint,
        )
        self.assertIn(
            "Disabled legacy HolyCode-managed",
            self.entrypoint,
        )

    def test_hermes_setting_fails_with_preservation_message(self):
        self.assertIn('if [ "${ENABLE_HERMES}" = "true" ]; then', self.entrypoint)
        self.assertIn("bundled Hermes is temporarily unavailable", self.entrypoint)
        self.assertIn("/home/opencode/.hermes is preserved", self.entrypoint)
        self.assertNotIn("contents.d/hermes", self.entrypoint)

    def test_chromium_sandbox_is_required(self):
        self.assertNotIn("--no-sandbox", self.dockerfile)

    def test_claude_auth_bind_mounts_are_git_bash_safe(self):
        self.assertIn("export MSYS_NO_PATHCONV=1", self.claude_auth)

    def test_protected_validation_uses_native_architecture_runners(self):
        self.assertIn("runner: ubuntu-24.04", self.protected)
        self.assertIn("runner: ubuntu-24.04-arm", self.protected)
        self.assertIn("Build and push attested candidate", self.protected)
        self.assertIn("Pull exact candidate digest", self.protected)
        self.assertIn("chromium-sandbox", self.dockerfile)
        self.assertIn("test -u /usr/lib/chromium/chrome-sandbox", self.dockerfile)

    def test_release_workflow_uses_v1_1_3_predecessor(self):
        self.assertIn("RELEASE_VERSION: v1.1.4", self.protected)
        self.assertIn("PREVIOUS_VERSION: v1.1.3", self.protected)
        self.assertIn(
            "coderluii/holycode:1.1.3@sha256:1a62f8e2f7a381c14bb84890a05bc04763f6804ac83e17e4dc022df0e5ef6e7f",
            self.protected,
        )
        self.assertIn("needs: protected-validation", self.publish)
        self.assertNotIn("./.github/workflows/protected-validation.yml", self.publish)
        self.assertIn("Download protected candidate digest", self.publish)
        self.assertNotIn("event=workflow_dispatch", self.publish)
        self.assertEqual(self.publish.count("docker/build-push-action"), 1)

    def test_upgrade_fixture_covers_stateful_paperclip_paths(self):
        expected = (
            "company_memberships",
            "agent_runtime_state",
            "plugin_config",
            "connection_grants",
            "0136_acpx_default_engine_migration",
            "0164_plugin_config_company_scope",
            "0182_connections_v3_schema_core",
            "0183_connection_user_authorization_state",
        )
        for value in expected:
            with self.subTest(value=value):
                self.assertIn(value, self.upgrade)

    def test_release_workflows_bind_and_promote_the_validated_candidate(self):
        self.assertIn('[ "$REQUESTED_REF" = "$GITHUB_SHA" ]', self.protected)
        self.assertIn('[ "$actual_sha" = "$(git rev-parse origin/main)" ]', self.protected)
        self.assertIn('ref: ${{ github.sha }}', self.protected)
        self.assertIn("docker pull --platform", self.protected)
        self.assertIn("scout-fixable.sarif", self.protected)
        self.assertIn("validate_scanner_findings.py", self.protected)
        self.assertIn("bash scripts/test_plugin_modes.sh", self.protected)
        self.assertIn("group: docker-release", self.publish)
        self.assertIn("cancel-in-progress: false", self.publish)
        self.assertIn("Require matching published GitHub release", self.publish)
        self.assertIn(".name == $tag", self.publish)
        self.assertIn("docker buildx imagetools create", self.publish)
        self.assertIn('[ "$expected_digest" = "$CANDIDATE_DIGEST" ]', self.publish)
        self.assertIn("git merge-base --is-ancestor", self.publish)
        self.assertIn("gh release upload", self.publish)

    def test_chromium_seccomp_migration_is_documented_everywhere(self):
        profile_url = (
            "https://raw.githubusercontent.com/CoderLuii/HolyCode/v1.1.3/"
            "config/chromium-seccomp.json"
        )
        for path in (ROOT / "docs" / "translations").glob("README.*.md"):
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertIn(profile_url, text)
                self.assertGreaterEqual(text.count("security_opt:"), 2)
        for name, text in (("README", self.readme), ("Docker Hub", self.dockerhub)):
            with self.subTest(document=name):
                self.assertIn(profile_url, text)
                self.assertGreaterEqual(text.count("security_opt:"), 2)

    def test_workflow_dependency_and_security_pins(self):
        checkout = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1"
        self.assertIn(checkout, self.publish)
        self.assertIn(checkout, self.protected)
        self.assertIn(checkout, self.pr_validation)
        self.assertIn(
            "bash scripts/validate_renovate_extraction.sh 44.2.3",
            self.pr_validation,
        )
        self.assertIn(
            "bash scripts/validate_renovate_extraction.sh 44.2.3",
            self.protected,
        )
        setup_node = (
            "actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0"
        )
        self.assertIn(setup_node, self.pr_validation)
        self.assertIn(setup_node, self.protected)
        self.assertIn("node-version: 24.18.0", self.pr_validation)
        self.assertIn("node-version: 24.18.0", self.protected)
        self.assertIn(
            "docker/login-action@dbcb813823bdd20940b903addbd779551569679f # v4.6.0",
            self.publish,
        )
        self.assertIn(
            "docker/login-action@dbcb813823bdd20940b903addbd779551569679f # v4.6.0",
            self.protected,
        )
        self.assertIn("Trivy fixable critical and high gate", self.protected)
        self.assertIn("Docker Scout fixable critical and high gate", self.protected)
        self.assertIn("severity: CRITICAL,HIGH", self.protected)
        self.assertIn("validate_security_exceptions.py", self.protected)
        self.assertIn("format: json", self.protected)
        self.assertIn("trivy-fixable.json", self.protected)

    def test_renovate_regenerates_the_hash_locked_python_requirements(self):
        self.assertIn("pip-compile", self.renovate["enabledManagers"])
        self.assertNotIn("pip_requirements", self.renovate["enabledManagers"])
        self.assertEqual(
            self.renovate["pip-compile"]["managerFilePatterns"],
            [
                r"/^config\/python-requirements\.lock$/",
                r"/^config\/python-seed-requirements\.lock$/",
            ],
        )

    def test_chromium_seccomp_profile_is_forced_to_lf(self):
        self.assertIn("config/chromium-seccomp.json text eol=lf", self.gitattributes)

    def test_lifecycle_policy_matches_release(self):
        policy = json.loads((ROOT / "config" / "npm-global-script-policy.json").read_text(encoding="utf-8"))
        self.assertEqual(policy["npmVersion"], "12.0.2")
        self.assertIn("@anthropic-ai/claude-code@2.1.220", policy["allowScripts"])
        self.assertIn("opencode-ai@1.18.9", policy["allowScripts"])
        self.assertIn("prisma@7.9.1", policy["blockedScripts"])
        self.assertIn("@prisma/engines@7.9.1", policy["blockedScripts"])
        self.assertNotIn("netlify-cli@26.2.0", policy["blockedScripts"])
        for decision in ("allowScripts", "blockedScripts"):
            for package_id, entry in policy[decision].items():
                with self.subTest(package_id=package_id):
                    self.assertRegex(entry["integrity"], r"^sha512-")
                    self.assertTrue(entry["architectures"])


if __name__ == "__main__":
    unittest.main()
