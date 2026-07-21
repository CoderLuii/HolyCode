import json
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
        cls.publish = (ROOT / ".github" / "workflows" / "docker-publish.yml").read_text(encoding="utf-8")
        cls.protected = (ROOT / ".github" / "workflows" / "protected-validation.yml").read_text(encoding="utf-8")
        cls.pr_validation = (ROOT / ".github" / "workflows" / "pr-validation.yml").read_text(encoding="utf-8")
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.dockerhub = (ROOT / "docs" / "dockerhub-description.md").read_text(encoding="utf-8")

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
        ]

        for script in scripts:
            with self.subTest(script=script.name):
                first_line = script.read_bytes().splitlines(keepends=True)[0]
                self.assertNotIn(b"\r\n", first_line)

    def test_release_dependency_pins(self):
        expected = (
            "ARG S6_OVERLAY_VERSION=3.2.3.2",
            "ARG FZF_VERSION=0.74.1",
            "ARG OPENCODE_VERSION=1.18.4",
            "ARG CLAUDE_CODE_VERSION=2.1.216",
            "ARG PAPERCLIP_VERSION=2026.707.0",
            "ARG PNPM_VERSION=11.15.1",
            "ARG VITE_VERSION=8.1.5",
            "ARG PRETTIER_VERSION=3.9.6",
            "ARG PRISMA_VERSION=7.9.0",
            "ARG LIGHTHOUSE_VERSION=13.4.1",
            "ARG WRANGLER_VERSION=4.112.0",
            "requests==2.34.2",
            "Pillow==12.3.0",
            "postgresql-client-17 redis-tools sqlite3",
            "matplotlib==3.11.1",
            "tqdm==4.69.0",
            "fastapi==0.139.2",
            "packaging==26.2",
            "wheel==0.47.0",
            "rich==15.0.0",
        )
        for value in expected:
            with self.subTest(value=value):
                self.assertIn(value, self.dockerfile)
        self.assertNotIn("postgresql-client redis-tools sqlite3", self.dockerfile)

    def test_github_cli_is_rebuilt_with_fixed_go_toolchain(self):
        self.assertIn(
            "FROM golang:1.26.5-trixie@sha256:"
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
        self.assertIn("COPY --from=github-cli-builder /out/gh /usr/local/bin/gh", self.dockerfile)
        self.assertNotIn("https://cli.github.com/packages", self.dockerfile)
        self.assertIn("expected_github_cli", self.smoke)
        self.assertIn('test "$(command -v gh)" = "/usr/local/bin/gh"', self.smoke)
        self.assertIn('gh version $EXPECTED_GITHUB_CLI', self.smoke)
        self.assertIn("! dpkg-query -W gh", self.smoke)

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
        ):
            with self.subTest(value=value):
                self.assertNotIn(value, self.dockerfile)

        for command in ("vercel", "concurrently", "lhci", "sharp"):
            with self.subTest(command=command):
                self.assertIn(f"! command -v {command}", self.smoke)

    def test_scanner_remediations_are_pinned(self):
        self.assertIn("ARG PIP_VERSION=26.1.2", self.dockerfile)
        self.assertIn("ARG PAPERCLIP_UNDICI_VERSION=6.27.0", self.dockerfile)
        self.assertIn("python3-pip python3-wheel", self.dockerfile)
        self.assertIn("undici@${PAPERCLIP_UNDICI_VERSION}", self.dockerfile)
        self.assertIn(
            "sha512-YmfV3YnEDzXRC5lZ2jWtWWHKGUm1zIt8AhesR1tens+HTNv+YZlN/dp6G727LOvMJ8xjP9Be7Y2Sdr96LDm+pg==",
            self.dockerfile,
        )
        self.assertIn(
            'grep -F "<policy domain=\\"coder\\" rights=\\"read|write\\" '
            'pattern=\\"{GIF,JPEG,PNG,WEBP}\\" />"',
            self.smoke,
        )
        self.assertIn("npm ls undici --all", self.dockerfile)
        self.assertIn("cursor_cloud_api_key_missing", self.smoke)

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

    def test_release_workflow_uses_v1_1_2_predecessor(self):
        self.assertIn("PREVIOUS_VERSION: v1.1.2", self.protected)
        self.assertIn(
            "coderluii/holycode:1.1.2@sha256:65740c4d8aa416217391f53de4be984ea9f8dfd5f10553dead94db402645b537",
            self.protected,
        )
        self.assertIn("Require successful protected validation for this commit", self.publish)
        self.assertIn("Download protected candidate digest", self.publish)
        self.assertNotIn("docker/build-push-action", self.publish)

    def test_release_workflows_bind_and_promote_the_validated_candidate(self):
        self.assertIn('[ "$REQUESTED_REF" = "$GITHUB_SHA" ]', self.protected)
        self.assertIn('ref: ${{ github.sha }}', self.protected)
        self.assertIn("docker pull --platform", self.protected)
        self.assertIn("scout-fixable.sarif", self.protected)
        self.assertIn("findings=\"$(jq '[.runs[].results[]?] | length'", self.protected)
        self.assertIn("group: docker-release", self.publish)
        self.assertIn("cancel-in-progress: false", self.publish)
        self.assertIn("Require matching published GitHub release", self.publish)
        self.assertIn(".name == $tag", self.publish)
        self.assertIn("docker buildx imagetools create", self.publish)
        self.assertIn('[ "$expected_digest" = "$CANDIDATE_DIGEST" ]', self.publish)

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
        self.assertIn("renovate@43.274.0", self.pr_validation)
        self.assertIn("Trivy fixable critical and high gate", self.protected)
        self.assertIn("Docker Scout fixable critical and high gate", self.protected)
        self.assertIn("severity: CRITICAL,HIGH", self.protected)

    def test_lifecycle_policy_matches_release(self):
        policy = json.loads((ROOT / "config" / "npm-global-script-policy.json").read_text(encoding="utf-8"))
        self.assertIn("@anthropic-ai/claude-code@2.1.216", policy["allowScripts"])
        self.assertIn("opencode-ai@1.18.4", policy["allowScripts"])
        self.assertIn("prisma@7.9.0", policy["blockedScripts"])
        self.assertIn("@prisma/engines@7.9.0", policy["blockedScripts"])
        self.assertIn("workerd@1.20260714.1", policy["blockedScripts"])
        for decision in ("allowScripts", "blockedScripts"):
            for package_id, entry in policy[decision].items():
                with self.subTest(package_id=package_id):
                    self.assertRegex(entry["integrity"], r"^sha512-")
                    self.assertTrue(entry["architectures"])


if __name__ == "__main__":
    unittest.main()
