import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReleaseContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        cls.entrypoint = (ROOT / "scripts" / "entrypoint.sh").read_text(encoding="utf-8")
        cls.bootstrap = (ROOT / "scripts" / "bootstrap.sh").read_text(encoding="utf-8")
        cls.smoke = (ROOT / "scripts" / "smoke_image.sh").read_text(encoding="utf-8")
        cls.claude_auth = (ROOT / "scripts" / "test_claude_auth.sh").read_text(encoding="utf-8")
        cls.plugin_modes = (ROOT / "scripts" / "test_plugin_modes.sh").read_text(encoding="utf-8")
        cls.upgrade = (ROOT / "scripts" / "test_upgrade_rollback.sh").read_text(
            encoding="utf-8"
        )
        cls.publish = (ROOT / ".github" / "workflows" / "docker-publish.yml").read_text(encoding="utf-8")
        cls.protected = cls.publish
        cls.pr_validation = (ROOT / ".github" / "workflows" / "pr-validation.yml").read_text(encoding="utf-8")
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.dockerhub = (ROOT / "docs" / "dockerhub-description.md").read_text(encoding="utf-8")
        cls.changelog = (ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
        cls.dependency_audit = (
            ROOT / "docs" / "dependency-audit-v1.1.8.md"
        )
        cls.notices = (ROOT / "THIRD-PARTY-NOTICES").read_text(encoding="utf-8")
        cls.gitattributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        cls.python_lock = (ROOT / "config" / "python-requirements.lock").read_text(encoding="utf-8")
        cls.python_seed_lock = (
            ROOT / "config" / "python-seed-requirements.lock"
        ).read_text(encoding="utf-8")
        cls.pip_pkg_resources_patch = (
            ROOT / "patches" / "pip-vendored-pkg-resources-78.1.1.patch"
        ).read_text(encoding="utf-8")
        cls.renovate = json.loads((ROOT / "renovate.json").read_text(encoding="utf-8"))
        cls.s6 = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "s6-overlay").rglob("*")
            if path.is_file()
        )

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
            "ARG GITHUB_CLI_VERSION=2.98.0",
            "ARG FZF_VERSION=0.74.3",
            "ARG LAZYGIT_VERSION=0.64.1",
            "ARG OPENCODE_VERSION=1.18.25",
            "ARG CLAUDE_CODE_VERSION=2.1.252",
            "ARG PAPERCLIP_VERSION=2026.824.1",
            "ARG OPENSPEC_VERSION=1.11.0",
            "ARG PAPERCLIP_UNDICI_VERSION=6.28.0",
            "ARG CLAUDE_AUTH_PLUGIN_VERSION=2.1.6",
            "ARG NPM_VERSION=12.0.2",
            "ARG NPM_BRACE_EXPANSION_VERSION=5.0.9",
            "ARG NPM_TAR_VERSION=7.5.22",
            "ARG PIP_VENDOR_MSGPACK_VERSION=1.2.1",
            "ARG PIP_VENDOR_PKG_RESOURCES_VERSION=78.1.1",
            "ARG SETUPTOOLS_VERSION=84.0.0",
            "ARG TSX_VERSION=4.23.13",
            "ARG PNPM_VERSION=11.25.0",
            "ARG VITE_VERSION=8.2.2",
            "ARG PRETTIER_VERSION=3.9.6",
            "ARG PRISMA_VERSION=7.10.0",
            "ARG PRISMA_DEEPMERGE_VERSION=8.0.0",
            "ARG PRISMA_MYSQL2_VERSION=3.22.0",
            "ARG LIGHTHOUSE_VERSION=13.4.1",
            "ARG WRANGLER_VERSION=4.127.1",
            "ARG ESLINT_VERSION=10.9.1",
            "requests==2.34.2",
            "pillow==12.3.0",
            "postgresql-client-17 redis-tools sqlite3",
            "matplotlib==3.11.1",
            "pandas==3.0.5",
            "tqdm==4.70.0",
            "fastapi==0.141.1",
            "playwright==1.62.0",
            "uvicorn==0.52.4",
            "packaging==26.3",
            "setuptools==84.0.0",
            "numpy==2.5.2",
            "markdown==3.10.3",
            "wheel==0.48.0",
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
        self.assertIn("bom.cdx.json", self.dockerfile)
        self.assertIn("msgpack==${PIP_VENDOR_MSGPACK_VERSION}", self.dockerfile)
        self.assertIn("PIP_VENDOR_PKG_RESOURCES", self.dockerfile)
        self.assertIn("pip-vendored-pkg-resources-78.1.1.patch", self.dockerfile)
        self.assertIn(
            "fcc17fd9cd898242f6b4adfaca46137a9edef687f43e6f78469692a5e70d851d",
            self.dockerfile,
        )
        self.assertIn("setuptools==$EXPECTED_PIP_VENDOR_PKG_RESOURCES", self.smoke)
        self.assertIn("import pip._vendor.pkg_resources", self.smoke)
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
            "FROM --platform=$BUILDPLATFORM golang:1.27.0-trixie@sha256:"
            "df98008ecd2b0ecc9f0a94d1b07e3564a9c92b555369b33d9b5f60d0765b2db7 "
            "AS github-cli-builder",
            self.dockerfile,
        )
        self.assertIn("ARG GITHUB_CLI_VERSION=2.98.0", self.dockerfile)
        self.assertIn(
            "ARG GITHUB_CLI_REF=a255baf71d13fe5947a4eb7ad521ffd412d64cee",
            self.dockerfile,
        )
        self.assertIn('test "$(git rev-parse HEAD)" = "${GITHUB_CLI_REF}"', self.dockerfile)
        self.assertIn('go version -m /out/gh | grep -F "go1.27.0"', self.dockerfile)
        self.assertIn(
            'test "$(go list -m -f \'{{.Version}}\' golang.org/x/mod)" = "v0.38.0"',
            self.dockerfile,
        )
        self.assertIn("go get golang.org/x/mod@v0.40.0", self.dockerfile)
        self.assertIn(
            'test "$(go list -m -f \'{{.Version}}\' golang.org/x/mod)" = "v0.40.0"',
            self.dockerfile,
        )
        self.assertIn(
            "go version -m /out/gh | grep -E "
            "'github.com/klauspost/compress[[:space:]]+v1\\.19\\.2'",
            self.dockerfile,
        )
        self.assertIn(
            "go version -m /out/gh | grep -E "
            "'golang.org/x/text[[:space:]]+v0\\.41\\.0'",
            self.dockerfile,
        )
        self.assertIn(
            "go version -m /out/gh | grep -E "
            "'golang.org/x/mod[[:space:]]+v0\\.40\\.0'",
            self.dockerfile,
        )
        self.assertNotIn("github-cli-modules.patch", self.dockerfile)
        self.assertIn(
            "FROM node:24.20.0-trixie-slim@sha256:"
            "50c3b2f6988dfc307b86e5301d69611af31f4789bdf232863b07d3b02fe55ae0",
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
            "ARG FZF_REF=15f64c492a08f0840b81540c7d1de35737448086",
            self.dockerfile,
        )
        self.assertIn(
            "ARG LAZYGIT_REF=fbe2379fa5831b1ce1a8a836a604652ffc14844f",
            self.dockerfile,
        )
        self.assertIn(
            "go version -m /out/fzf | grep -E "
            "'golang.org/x/sys[[:space:]]+v0\\.44\\.0'",
            self.dockerfile,
        )
        self.assertIn(
            "go version -m /out/lazygit | grep -E "
            "'golang.org/x/text[[:space:]]+v0\\.40\\.0'",
            self.dockerfile,
        )
        self.assertNotIn("lazygit-x-text-0.39.0.patch", self.dockerfile)
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
        self.assertIn("ARG PIP_VENDOR_PKG_RESOURCES_VERSION=78.1.1", self.dockerfile)
        self.assertIn("pip-vendored-pkg-resources-78.1.1.patch", self.dockerfile)
        self.assertIn(
            "fcc17fd9cd898242f6b4adfaca46137a9edef687f43e6f78469692a5e70d851d",
            self.dockerfile,
        )
        self.assertIn("setuptools==$EXPECTED_PIP_VENDOR_PKG_RESOURCES", self.smoke)
        self.assertIn("import pip._vendor.pkg_resources", self.smoke)
        self.assertEqual(self.pr_validation.count("timeout: 15m"), 2)
        self.assertEqual(self.publish.count("timeout: 15m"), 2)
        hunk_header = re.compile(r"^@@ -(\d+),(\d+) \+(\d+),(\d+) @@")
        lines = self.pip_pkg_resources_patch.splitlines()
        headers = [index for index, line in enumerate(lines) if line.startswith("@@ ")]
        self.assertGreater(len(headers), 2)
        for position, index in enumerate(headers):
            match = hunk_header.match(lines[index])
            self.assertIsNotNone(match, lines[index])
            end = headers[position + 1] if position + 1 < len(headers) else len(lines)
            body = lines[index + 1 : end]
            old_count = sum(line.startswith((" ", "-")) for line in body)
            new_count = sum(line.startswith((" ", "+")) for line in body)
            self.assertEqual(old_count, int(match.group(2)), lines[index])
            self.assertEqual(new_count, int(match.group(4)), lines[index])
        self.assertIn("bom.cdx.json", self.dockerfile)
        self.assertIn("ARG PAPERCLIP_UNDICI_VERSION=6.28.0", self.dockerfile)
        self.assertIn("ARG NPM_TAR_VERSION=7.5.22", self.dockerfile)
        self.assertNotIn("python3 python3-pip python3-venv", self.dockerfile)
        self.assertIn("python3 python3-venv", self.dockerfile)
        self.assertIn("python3 -m venv /tmp/holycode-pip-bootstrap", self.dockerfile)
        self.assertIn("--target /usr/local/lib/python3.13/dist-packages", self.dockerfile)
        self.assertIn("${db:Status-Status}' python3-pip", self.dockerfile)
        self.assertIn("${db:Status-Status}' python3-setuptools", self.dockerfile)
        self.assertIn('pip --version | grep -F "pip 26.2.1"', self.smoke)
        self.assertIn("-f=\\${db:Status-Status} python3-pip", self.smoke)
        self.assertIn("-f=\\${db:Status-Status} python3-setuptools", self.smoke)
        self.assertIn("for attempt in 1 2 3", self.dockerfile)
        self.assertIn("if go mod download; then break; fi", self.dockerfile)
        self.assertIn("ARG PRISMA_DEEPMERGE_VERSION=8.0.0", self.dockerfile)
        self.assertIn("io.holycode.version.prisma-deepmerge-ts", self.dockerfile)
        self.assertIn("io.holycode.version.prisma-mysql2", self.dockerfile)
        self.assertIn(
            "sha512-ICNjaP0ML+eSdEpJYQC46XiAn/UjAdwbEl0dE8p85ZTeNDinN4Kd4+9jS4OSAuH7st6eC7rQhsqTF5zIDaUm2g==",
            self.dockerfile,
        )
        self.assertIn(
            'test "$(npm view "@prisma/config@${PRISMA_VERSION}" dependencies.deepmerge-ts)" = "7.1.5"',
            self.dockerfile,
        )
        self.assertIn("PRISMA_CONFIG_PACKAGE", self.dockerfile)
        self.assertIn('test "$(npm view "prisma@${PRISMA_VERSION}" dependencies.mysql2)" = "3.15.3"', self.dockerfile)
        self.assertIn("sha512-4jaJYBObj7FhD3lnZhqX1yDMuZN4mQNz+IolDySDXT7fbozMBpeGQNcuWXKUqo4ahkAEfkjUHPjnwuDI0/6VKw==", self.dockerfile)
        self.assertIn('npm install --prefix "$PRISMA_MYSQL2_DIR" --ignore-scripts --package-lock=false --omit=dev', self.dockerfile)
        self.assertIn("npm ls deepmerge-ts mysql2 --all", self.dockerfile)
        self.assertIn("expected_prisma_deepmerge", self.smoke)
        self.assertIn("EXPECTED_PRISMA_DEEPMERGE", self.smoke)
        self.assertIn("expected_prisma_mysql2", self.smoke)
        self.assertIn("EXPECTED_PRISMA_MYSQL2", self.smoke)
        self.assertIn(
            "--require-hashes -r /usr/local/share/holycode/python-seed-requirements.lock",
            self.dockerfile,
        )
        for package in ("pip==26.2.1", "setuptools==84.0.0", "packaging==26.3", "wheel==0.48.0"):
            with self.subTest(package=package):
                self.assertIn(package, self.python_seed_lock)
        self.assertIn(
            "assert setuptools.__version__ == \"84.0.0\"",
            self.dockerfile,
        )
        for assertion in (
            'assert metadata.version("uvicorn") == "0.52.4"',
            'assert metadata.version("packaging") == "26.3"',
            'assert metadata.version("pip") == "26.2.1"',
            'assert metadata.version("setuptools") == "84.0.0"',
        ):
            with self.subTest(assertion=assertion):
                self.assertIn(assertion, self.smoke)
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

    def test_npm_ip_address_overlay_is_integrity_bound_and_exercised(self):
        self.assertIn("ARG NPM_IP_ADDRESS_VERSION=10.7.0", self.dockerfile)
        self.assertIn(
            "sha512-BGFsyJd5mpXp3rK6jIdADLNgpJUK1jnjzvYF8lK+VyDab9JAmqN0YOKDdP17HlgKb2+ehPgDc8EtnRLbGCAMhA==",
            self.dockerfile,
        )
        self.assertIn(
            "/usr/local/lib/node_modules/npm/node_modules/ip-address",
            self.dockerfile,
        )
        self.assertIn(
            "/usr/local/lib/node_modules/npm/node_modules/socks/package.json",
            self.dockerfile,
        )
        owner_assertion = (
            'if(pkg.version!=="2.8.9" || '
            'pkg.dependencies["ip-address"]!=="^10.1.1")'
        )
        self.assertIn(owner_assertion, self.dockerfile)
        self.assertIn("npm ls ip-address --all", self.dockerfile)
        self.assertIn("io.holycode.version.npm-ip-address", self.dockerfile)
        self.assertIn("expected_npm_ip_address", self.smoke)
        self.assertIn("EXPECTED_NPM_IP_ADDRESS", self.smoke)
        smoke_owner_assertion = (
            'if(pkg.version!==\\"2.8.9\\" || '
            'pkg.dependencies[\\"ip-address\\"]!==\\"^10.1.1\\")'
        )
        self.assertIn(smoke_owner_assertion, self.smoke)
        self.assertIn("npm ls ip-address --all", self.smoke)
        runtime_assertion = 'test "$(npm prefix -g)" = "/usr/local"'
        self.assertIn(runtime_assertion, self.dockerfile)
        self.assertIn(runtime_assertion, self.smoke)
        self.assertNotIn("npm --help >/dev/null", self.dockerfile)
        self.assertNotIn("npm --help >/dev/null", self.smoke)

    def test_pm2_js_yaml_owner_and_runtime_are_validated_without_rewrite(self):
        self.assertIn("ARG PM2_JS_YAML_VERSION=4.3.1", self.dockerfile)
        self.assertIn(
            "sha512-CY6crGq313MX8GkwvB7tzgp99vjQxY1++5y10/BKN/GUfHqWaOGQMNZkBvqSzsZKWk/ijwHlWzzkLulsGHhjWQ==",
            self.dockerfile,
        )
        self.assertIn(
            "/usr/local/lib/node_modules/pm2/node_modules/js-yaml",
            self.dockerfile,
        )
        self.assertIn(
            "/usr/local/lib/node_modules/pm2/package.json",
            self.dockerfile,
        )
        self.assertIn(
            'npm view pm2@7.0.4 dependencies.js-yaml)" = "${PM2_JS_YAML_VERSION}',
            self.dockerfile,
        )
        self.assertIn('dependencies["js-yaml"]', self.dockerfile)
        self.assertIn("npm ls js-yaml --all", self.dockerfile)
        self.assertNotIn('dependencies["js-yaml"]!=="4.3.0"', self.dockerfile)
        self.assertNotIn("PM2_JS_YAML_TARBALL", self.dockerfile)
        self.assertNotIn('rm -rf "$PM2_JS_YAML_DIR"', self.dockerfile)
        self.assertIn("io.holycode.version.pm2-js-yaml", self.dockerfile)
        self.assertIn("expected_pm2_js_yaml", self.smoke)
        self.assertIn("EXPECTED_PM2_JS_YAML", self.smoke)
        self.assertIn("npm ls js-yaml --all", self.smoke)
        self.assertIn("PM2_HOME=/tmp/holycode-smoke-pm2", self.smoke)

    def test_checksum_bound_external_downloads_have_bounded_retry_window(self):
        curl = shutil.which("curl")
        self.assertIsNotNone(curl)

        def exercise_retry_policy(failures, retry_max_time, payload=b"retry recovered\n", truncate=False):
            request_times = []

            class Handler(BaseHTTPRequestHandler):
                def do_GET(self):
                    request_times.append(time.monotonic())
                    if truncate:
                        partial = b"partial"
                        self.send_response(200)
                        self.send_header("Content-Length", str(len(partial) + 32))
                        self.end_headers()
                        self.wfile.write(partial)
                        self.close_connection = True
                        return
                    if len(request_times) <= failures:
                        self.send_response(503)
                        self.send_header("Content-Length", "0")
                        self.end_headers()
                        return
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)

                def log_message(self, _format, *_args):
                    return

            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    output = Path(temp_dir) / "asset"
                    started = time.monotonic()
                    result = subprocess.run(
                        [
                            curl,
                            "--disable",
                            "--retry",
                            "8",
                            "--retry-all-errors",
                            "--retry-max-time",
                            str(retry_max_time),
                            "--remove-on-error",
                            "--noproxy",
                            "*",
                            "--connect-timeout",
                            "1",
                            "--max-time",
                            "1",
                            "-fsSL",
                            "-o",
                            str(output),
                            f"http://127.0.0.1:{server.server_port}/asset",
                        ],
                        capture_output=True,
                        check=False,
                        text=True,
                    )
                    elapsed = time.monotonic() - started
                    output_exists = output.exists()
                    downloaded = output.read_bytes() if output_exists else b""
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
            return result, request_times, elapsed, output_exists, downloaded

        recovered, request_times, elapsed, output_exists, payload = exercise_retry_policy(2, 10)
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        self.assertTrue(output_exists)
        self.assertEqual(payload, b"retry recovered\n")
        self.assertEqual(len(request_times), 3)
        self.assertGreaterEqual(request_times[1] - request_times[0], 0.8)
        self.assertGreaterEqual(request_times[2] - request_times[1], 1.8)
        self.assertLess(elapsed, 8)

        exhausted, request_times, elapsed, output_exists, _payload = exercise_retry_policy(
            0, 3, truncate=True
        )
        self.assertNotEqual(exhausted.returncode, 0)
        self.assertFalse(output_exists)
        self.assertGreaterEqual(len(request_times), 2)
        self.assertLessEqual(len(request_times), 3)
        self.assertGreaterEqual(elapsed, 2.8)
        self.assertLess(elapsed, 5)

        expected_sha256 = hashlib.sha256(b"expected\n").hexdigest()
        wrong, request_times, _elapsed, output_exists, payload = exercise_retry_policy(
            0, 10, payload=b"wrong\n"
        )
        self.assertEqual(wrong.returncode, 0, wrong.stderr)
        self.assertTrue(output_exists)
        checksum_matches = hashlib.sha256(payload).hexdigest() == expected_sha256
        self.assertFalse(checksum_matches)
        self.assertEqual(len(request_times), 1)

        retry_flags = (
            "curl --disable --retry 8 --retry-all-errors --retry-max-time 300 "
            "--remove-on-error --connect-timeout 15 --max-time 300 -fsSL -o /tmp/"
        )
        self.assertEqual(self.dockerfile.count(retry_flags), 6)
        self.assertNotIn("--retry-delay", self.dockerfile)
        self.assertNotIn("curl -fsSL -o /tmp/", self.dockerfile)
        for checksum in (
            "5379750ed30a84bbd2e2dd74847ba6b5bd29cd0b2e3ea2ec58049b57eb2eda12",
            "${S6_ARCH_SHA256}",
            "${DELTA_SHA256}",
            "${EZA_SHA256}",
            "${PIP_VENDOR_MSGPACK_SHA256}",
            "${PIP_VENDOR_PKG_RESOURCES_SHA256}",
        ):
            with self.subTest(checksum=checksum):
                self.assertIn(f'{checksum}  /tmp/', self.dockerfile)

    def test_claude_auth_is_installed_from_verified_offline_payload(self):
        self.assertIn("ARG CLAUDE_AUTH_PLUGIN_VERSION=2.1.6", self.dockerfile)
        self.assertNotIn("opencode-claude-auth@2.1.5", self.plugin_modes)
        self.assertIn("opencode-claude-auth@2.1.6", self.plugin_modes)
        self.assertIn(
            "sha512-PVHMBoGms/e2cRDXi1gMx4N8UK4ZSBaviNO7UfheXm5mEW+PnFe7H1brXK5pDjvm1na"
            "Gn9AntWUNIhOeJnyhvA==",
            self.dockerfile,
        )
        self.assertIn('dist.integrity)" =', self.dockerfile)
        self.assertIn("npm pack --silent --pack-destination /tmp", self.dockerfile)
        self.assertIn("/usr/local/share/holycode/plugins/opencode-claude-auth", self.dockerfile)
        self.assertIn('CLAUDE_AUTH_PLUGIN_VERSION="2.1.6"', self.entrypoint)
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
        self.assertIn("workflow_dispatch:", self.pr_validation)
        self.assertIn("if: github.event_name == 'workflow_dispatch'", self.pr_validation)
        self.assertIn("test \"$GITHUB_REF\" = 'refs/heads/main'", self.pr_validation)
        self.assertNotIn("github.event_name == 'pull_request' || github.ref", self.pr_validation)
        self.assertIn("runner: ubuntu-24.04", self.protected)
        self.assertIn("runner: ubuntu-24.04-arm", self.protected)
        self.assertIn("Build and push attested candidate", self.protected)
        self.assertIn("Pull exact candidate digest", self.protected)
        self.assertIn("chromium-sandbox", self.dockerfile)
        self.assertIn("test -u /usr/lib/chromium/chrome-sandbox", self.dockerfile)

    def test_v1_1_8_uses_v1_1_7_as_its_git_predecessor(self):
        self.assertIn("RELEASE_VERSION: v1.1.8", self.protected)
        self.assertIn("PREVIOUS_VERSION: v1.1.7", self.protected)
        self.assertIn(
            "coderluii/holycode:1.1.7@sha256:4e20d9eac20afb4e779b98037a923201027008f0acee5617fe10cbf90f1a4a41",
            self.protected,
        )
        self.assertIn("needs: protected-validation", self.publish)
        self.assertNotIn("./.github/workflows/protected-validation.yml", self.publish)
        self.assertIn("Download protected candidate digest", self.publish)
        self.assertNotIn("event=workflow_dispatch", self.publish)
        self.assertEqual(self.publish.count("docker/build-push-action"), 1)
        self.assertNotIn("config/security-exceptions-v1.1.4.json", self.protected)

    def test_v1_1_8_release_metadata_is_documented(self):
        self.assertRegex(self.changelog, r"(?m)^## \[1\.1\.8\] - \d{2}/\d{2}/\d{4}$")
        self.assertTrue(self.dependency_audit.is_file())
        audit = self.dependency_audit.read_text(encoding="utf-8")
        self.assertIn("Git predecessor `v1.1.7`", audit)
        self.assertIn(
            "`coderluii/holycode:1.1.7@sha256:4e20d9eac20afb4e779b98037a923201027008f0acee5617fe10cbf90f1a4a41`",
            audit,
        )
        self.assertIn("v1.1.8 release pins", self.readme)
        self.assertIn("dependency-audit-v1.1.8.md", self.readme)
        self.assertIn("v1.1.8", self.dockerhub)
        self.assertIn("js-yaml 4.3.1", self.notices)
        self.assertIn("ip-address 10.7.0", self.notices)

    def test_openspec_is_pinned_installed_and_telemetry_disabled(self):
        self.assertIn(
            "# renovate: datasource=npm depName=@fission-ai/openspec\n"
            "ARG OPENSPEC_VERSION=1.11.0",
            self.dockerfile,
        )
        self.assertIn(
            "io.holycode.version.openspec=${OPENSPEC_VERSION}",
            self.dockerfile,
        )
        self.assertIn("ENV OPENSPEC_TELEMETRY=0", self.dockerfile)
        self.assertRegex(
            self.dockerfile,
            r'RUN npm (?:i|install) -g --ignore-scripts[^\n]*(?:\\\n[^\n]*)*'
            r'"@fission-ai/openspec@\$\{OPENSPEC_VERSION\}"',
        )

    def test_openspec_smoke_checks_exact_binary_and_package_versions(self):
        self.assertIn(
            'expected_openspec="$(image_label io.holycode.version.openspec)"',
            self.smoke,
        )
        self.assertIn('-e EXPECTED_OPENSPEC="$expected_openspec"', self.smoke)
        self.assertIn(
            'test "$(openspec --version)" = "$EXPECTED_OPENSPEC"',
            self.smoke,
        )
        self.assertIn(
            'npm ls -g --depth=0 "@fission-ai/openspec@$EXPECTED_OPENSPEC"',
            self.smoke,
        )

    def test_openspec_is_never_initialized_automatically_at_startup(self):
        for name, source in (
            ("Dockerfile", self.dockerfile),
            ("entrypoint", self.entrypoint),
            ("bootstrap", self.bootstrap),
            ("s6", self.s6),
        ):
            with self.subTest(source=name):
                self.assertNotRegex(source, r"\bopenspec\s+init\b")

    def test_openspec_smoke_covers_explicit_safe_initialization(self):
        self.assertIn("openspec init", self.smoke)
        self.assertIn("--tools opencode", self.smoke)
        self.assertIn("--network none", self.smoke)
        self.assertIn("--user 1000:1000", self.smoke)
        self.assertIn("cleanup_openspec_workspace()", self.smoke)
        self.assertIn("--network none --user 0:0 --entrypoint sh", self.smoke)
        self.assertIn("find /workspace -mindepth 1 -delete", self.smoke)
        self.assertIn("trap cleanup_openspec_workspace EXIT", self.smoke)
        self.assertIn("openspec list --json", self.smoke)
        self.assertGreaterEqual(self.smoke.count("openspec init --tools opencode"), 2)
        self.assertIn("snapshot_openspec_workspace", self.smoke)
        self.assertIn("openspec_snapshot_before", self.smoke)
        self.assertIn("openspec_snapshot_after", self.smoke)
        self.assertIn(
            'test "$openspec_snapshot_before" = "$openspec_snapshot_after"',
            self.smoke,
        )
        self.assertRegex(
            self.smoke,
            r'docker run[^\n]*(?:\\\n[^\n]*)*--network none'
            r'(?:[^\n]*\\\n)*[^\n]*--user 1000:1000'
            r'[\s\S]*?openspec init --tools opencode'
            r'[\s\S]*?openspec list --json'
            r'[\s\S]*?openspec init --tools opencode',
        )

    def test_openspec_upgrade_fixture_proves_startup_does_not_mutate_projects(self):
        self.assertIn("openspec_startup_no_mutation=true", self.upgrade)
        self.assertIn("--user 2345:2345", self.upgrade)
        self.assertIn("--user 0:0", self.upgrade)
        self.assertIn('chown 2345:2345 /workspace', self.upgrade)
        self.assertIn('install -o 2345 -g 2345 -m 0644 /dev/null /workspace/.holycode-openspec-fixture', self.upgrade)
        self.assertIn('rm -f /workspace/.holycode-openspec-fixture', self.upgrade)
        self.assertGreaterEqual(self.upgrade.count('chmod 0755 /workspace'), 1)
        self.assertIn('test -w /workspace', self.upgrade)
        self.assertIn('OpenSpec fixture is not writable by 2345:2345', self.upgrade)
        self.assertIn("openspec_before", self.upgrade)
        self.assertIn("openspec_after", self.upgrade)
        self.assertIn('find /workspace -xdev -printf "%P|%y|%m|%U:%G', self.upgrade)
        self.assertIn('find /workspace -xdev -type f -print0', self.upgrade)
        self.assertRegex(
            self.upgrade,
            r'start_stack "\$baseline_name"[^\n]*\n'
            r'[\s\S]*?openspec_before=.*(?:snapshot_openspec_volume|sha256sum|tar)[^\n]*\n'
            r'[\s\S]*?start_stack "\$upgrade_name"[^\n]*\n'
            r'[\s\S]*?openspec_after=.*(?:snapshot_openspec_volume|sha256sum|tar)[^\n]*\n'
            r'[\s\S]*?\[ "\$openspec_before" = "\$openspec_after" \]',
        )

    def test_openspec_is_documented_and_attributed(self):
        self.assertIn("OpenSpec", self.readme)
        self.assertIn("@fission-ai/openspec", self.dependency_audit.read_text(encoding="utf-8"))
        self.assertIn("OpenSpec", self.dockerhub)
        self.assertIn("OpenSpec", self.changelog)
        self.assertIn("OpenSpec", self.notices)
        self.assertIn("https://github.com/Fission-AI/OpenSpec", self.notices)

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
        self.assertIn("paperclip_migration=false", self.upgrade)
        self.assertIn(
            'previous_paperclip_version" != "$current_paperclip_version',
            self.upgrade,
        )

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
            "bash scripts/validate_renovate_extraction.sh 44.56.0",
            self.pr_validation,
        )
        self.assertIn(
            "bash scripts/validate_renovate_extraction.sh 44.56.0",
            self.protected,
        )
        setup_node = (
            "actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0"
        )
        self.assertIn(setup_node, self.pr_validation)
        self.assertIn(setup_node, self.protected)
        self.assertIn("node-version: 24.20.0", self.pr_validation)
        self.assertIn("node-version: 24.20.0", self.protected)
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
        self.assertNotIn("--exceptions", self.protected)
        self.assertIn("format: json", self.protected)
        self.assertIn("trivy-fixable.json", self.protected)

    def test_pr_validation_covers_both_native_architectures(self):
        self.assertIn("runner: ubuntu-24.04", self.pr_validation)
        self.assertIn("runner: ubuntu-24.04-arm", self.pr_validation)
        self.assertIn("platform: linux/amd64", self.pr_validation)
        self.assertIn("platform: linux/arm64", self.pr_validation)
        self.assertIn("bash scripts/smoke_image.sh", self.pr_validation)
        self.assertIn("bash scripts/test_plugin_modes.sh", self.pr_validation)

    def test_manual_pre_tag_validation_runs_native_scanners_and_uploads_evidence(self):
        for value in (
            "scout_arch: amd64",
            "scout_arch: arm64",
            "scout_sha256: f4e2814bd61040365153d5b964b144cb2dc6ee536a68b5bac4cadf00fc0ec34b",
            "scout_sha256: 8b21594c72d4d9403a82a49e9dbdfc04c27c6a21933906f1eefbb0beabe22d58",
            "SCOUT_VERSION: 1.24.0",
            'docker-scout cves "sbom://$SCOUT_SBOM"',
            "--scanner scout",
            "--scanner trivy",
            "version: v0.74.0",
            "scanners: vuln,secret",
            "ignore-unfixed: true",
            "holycode-pretag-${{ github.sha }}-${{ matrix.suffix }}-evidence",
            "holycode-${{ matrix.suffix }}.commit-sha.txt",
            "holycode-${{ matrix.suffix }}.dpkg-inventory.txt",
            "holycode-${{ matrix.suffix }}.image-id.txt",
            "holycode-${{ matrix.suffix }}.scout-fixable.sarif",
            "holycode-${{ matrix.suffix }}.trivy-fixable.json",
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.pr_validation)

        manual_steps = (
            "Install Trivy CLI",
            "Generate pre-tag SPDX SBOM for Docker Scout",
            "Install Docker Scout CLI for pre-tag validation",
            "Login to Docker Hub for pre-tag Docker Scout",
            "Generate pre-tag Docker Scout vulnerability reports",
            "Docker Scout pre-tag fixable critical and high gate",
            "Generate pre-tag Trivy vulnerability report",
            "Trivy pre-tag fixable critical and high gate",
            "Validate pre-tag Trivy fixable critical and high findings",
            "Collect pre-tag architecture evidence",
            "Upload pre-tag architecture evidence",
        )
        for name in manual_steps:
            with self.subTest(step=name):
                self.assertRegex(
                    self.pr_validation,
                    rf"- name: {re.escape(name)}\n"
                    rf"(?:\s+id: [^\n]+\n)?"
                    rf"\s+if: (?:always\(\) && )?github\.event_name == 'workflow_dispatch'",
                )

    def test_scanner_cli_downloads_have_bounded_retry_and_integrity_gates(self):
        retry_flags = (
            "curl --disable --proto '=https' --tlsv1.2 --retry 8 --retry-all-errors "
            "--retry-max-time 300 --remove-on-error"
        )
        workflows = (
            (
                self.pr_validation,
                "Generate pre-tag SPDX SBOM for Docker Scout",
                "Install Docker Scout CLI for pre-tag validation",
            ),
            (self.protected, "Generate SPDX SBOM for Docker Scout", "Install Docker Scout CLI"),
        )
        for workflow, trivy_next_step, scout_step_name in workflows:
            for step_name, next_step_name in (
                ("Install Trivy CLI", trivy_next_step),
                (scout_step_name, "Login to Docker Hub"),
            ):
                with self.subTest(step=step_name):
                    step = re.search(
                        rf"- name: {re.escape(step_name)}\n(?P<body>.*?)"
                        rf"\n      - name: {re.escape(next_step_name)}",
                        workflow,
                        re.DOTALL,
                    )
                    self.assertIsNotNone(step)
                    body = step.group("body")
                    normalized_body = re.sub(r"\s+", " ", body.replace("\\\n", " "))
                    self.assertIn(retry_flags, normalized_body)
                    self.assertIn("--connect-timeout 15 --max-time 300", normalized_body)
                    self.assertNotIn("--retry-delay", normalized_body)
                    self.assertLess(
                        body.index("curl --disable"),
                        body.index("sha256sum --check --strict"),
                    )
                    self.assertLess(
                        body.index("sha256sum --check --strict"), body.index("tar -xzf")
                    )

        for workflow in (self.pr_validation, self.protected):
            for value in (
                "trivy_arch: 64bit",
                "trivy_sha256: 2ae6fe3ee734b7fdf11335663e18c75ea12dccc76062f09f164a3b0f8be4371a",
                "trivy_arch: ARM64",
                "trivy_sha256: b94ce1976bbf3c15b514b605ee88be7c6d94a29be2302847ff01cb794d47aad5",
                "TRIVY_VERSION: 0.74.0",
                "aquasecurity/trivy/releases/download/v${TRIVY_VERSION}",
            ):
                with self.subTest(value=value):
                    self.assertIn(value, workflow)
        self.assertEqual(self.pr_validation.count("skip-setup-trivy: true"), 3)
        self.assertEqual(self.protected.count("skip-setup-trivy: true"), 3)

    def test_manual_scanner_failures_preserve_both_reports_before_failing(self):
        for step_name, step_id in (
            ("Docker Scout pre-tag fixable critical and high gate", "scout_gate"),
            ("Validate pre-tag Trivy fixable critical and high findings", "trivy_gate"),
        ):
            with self.subTest(step=step_name):
                self.assertRegex(
                    self.pr_validation,
                    rf"- name: {re.escape(step_name)}\n"
                    rf"\s+id: {step_id}\n"
                    rf"\s+if: github\.event_name == 'workflow_dispatch'\n"
                    rf"\s+continue-on-error: true",
                )

        for step_name in (
            "Collect pre-tag architecture evidence",
            "Upload pre-tag architecture evidence",
            "Enforce pre-tag scanner gates",
        ):
            with self.subTest(step=step_name):
                self.assertRegex(
                    self.pr_validation,
                    rf"- name: {re.escape(step_name)}\n"
                    rf"\s+if: always\(\) && github\.event_name == 'workflow_dispatch'",
                )

        self.assertIn("SCOUT_GATE_OUTCOME: ${{ steps.scout_gate.outcome }}", self.pr_validation)
        self.assertIn("TRIVY_GATE_OUTCOME: ${{ steps.trivy_gate.outcome }}", self.pr_validation)
        self.assertIn('test "$SCOUT_GATE_OUTCOME" = "success"', self.pr_validation)
        self.assertIn('test "$TRIVY_GATE_OUTCOME" = "success"', self.pr_validation)

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
        self.assertIn("@anthropic-ai/claude-code@2.1.252", policy["allowScripts"])
        self.assertIn("opencode-ai@1.18.25", policy["allowScripts"])
        self.assertEqual(
            policy["blockedScripts"]["esbuild@0.28.1"]["integrity"],
            "sha512-HrJrvZv5ayxBzPfwphOoNzkzOIIlifzk0KJrGK2c8R4+LKpMtpYLQeUdjnwjWv/LZlkH2laZk+4w78pi99D4Vw==",
        )
        self.assertIn("Wrangler 4.127.1", policy["blockedScripts"]["esbuild@0.28.1"]["reason"])
        self.assertIn("esbuild@0.28.2", policy["blockedScripts"])
        self.assertIn("workerd@1.20260828.1", policy["blockedScripts"])
        self.assertIn("prisma@7.10.0", policy["blockedScripts"])
        self.assertIn("@prisma/engines@7.10.0", policy["blockedScripts"])
        self.assertNotIn("netlify-cli@26.2.0", policy["blockedScripts"])
        for decision in ("allowScripts", "blockedScripts"):
            for package_id, entry in policy[decision].items():
                with self.subTest(package_id=package_id):
                    self.assertRegex(entry["integrity"], r"^sha512-")
                    self.assertTrue(entry["architectures"])


if __name__ == "__main__":
    unittest.main()
