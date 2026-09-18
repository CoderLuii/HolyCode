import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import textwrap
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
        cls.workflow_pin_validator = (
            ROOT / "scripts" / "validate_workflow_pins.py"
        ).read_text(encoding="utf-8")
        cls.renovate_extraction = (
            ROOT / "scripts" / "validate_renovate_extraction.sh"
        ).read_text(encoding="utf-8")
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.dockerhub = (ROOT / "docs" / "dockerhub-description.md").read_text(encoding="utf-8")
        cls.changelog = (ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
        cls.dependency_audit = (
            ROOT / "docs" / "dependency-audit-v1.2.2.md"
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
            "ARG GITHUB_CLI_VERSION=2.101.0",
            "ARG FZF_VERSION=0.74.4",
            "ARG LAZYGIT_VERSION=0.65.1",
            "ARG OPENCODE_VERSION=1.18.31",
            "ARG CLAUDE_CODE_VERSION=2.1.276",
            "ARG PAPERCLIP_VERSION=2026.831.1",
            "ARG OPENSPEC_VERSION=1.13.1",
            "ARG PAPERCLIP_UNDICI_VERSION=6.28.1",
            "ARG CLAUDE_AUTH_PLUGIN_VERSION=2.2.0",
            "ARG TYPESCRIPT_VERSION=6.0.3",
            "ARG NPM_VERSION=12.0.2",
            "ARG NPM_BRACE_EXPANSION_VERSION=5.0.12",
            "ARG NPM_TAR_VERSION=7.5.22",
            "ARG PM2_JS_YAML_VERSION=4.3.2",
            "ARG PIP_VENDOR_MSGPACK_VERSION=1.2.2",
            "ARG PIP_VENDOR_PKG_RESOURCES_VERSION=78.1.1",
            "ARG SETUPTOOLS_VERSION=84.0.0",
            "ARG TSX_VERSION=4.23.13",
            "ARG PNPM_VERSION=12.4.2",
            "ARG VITE_VERSION=8.3.0",
            "ARG PRETTIER_VERSION=3.9.8",
            "ARG PRISMA_VERSION=7.10.0",
            "ARG PRISMA_DEEPMERGE_VERSION=8.0.2",
            "ARG PRISMA_MYSQL2_VERSION=3.24.4",
            "ARG LIGHTHOUSE_VERSION=13.4.1",
            "ARG WRANGLER_VERSION=4.134.0",
            "ARG WRANGLER_MINIFLARE_VERSION=5.20260917.0-alpha",
            "ARG WRANGLER_SHARP_VERSION=0.35.4",
            "ARG WRANGLER_SHARP_LIBVIPS_VERSION=1.3.3",
            "ARG ESLINT_VERSION=10.10.0",
            "requests==2.34.2",
            "pillow==12.3.0",
            "postgresql-client-17 redis-tools sqlite3",
            "matplotlib==3.11.2",
            "fonttools==4.65.0",
            "pandas==3.0.6",
            "tqdm==4.70.1",
            "fastapi==0.141.1",
            "playwright==1.63.0",
            "uvicorn==0.53.0",
            "packaging==26.3",
            "setuptools==84.0.0",
            "numpy==2.5.3",
            "lxml==6.1.3",
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
            "9eb0b0e602064527a045ea28c4f174ed69383587e29cebe28947e3b84106eb2a",
            self.dockerfile,
        )
        self.assertIn("bom.cdx.json", self.dockerfile)
        self.assertIn("msgpack==${PIP_VENDOR_MSGPACK_VERSION}", self.dockerfile)
        self.assertIn('msgpack.unpackb(msgpack.packb({"holycode": True}))', self.dockerfile)
        self.assertIn('msgpack.unpackb(msgpack.packb({\\"holycode\\": True}))', self.smoke)
        for value in (
            "from pip._vendor.msgpack import fallback",
            "memoryview(interleaved)[::2]",
            "except msgpack.ExtraData",
            'fallback.unpackb(b"\\xd9")',
            "msgpack.Timestamp(0, 999999999)",
            "msgpack.Timestamp(0, 1000000000)",
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.smoke)
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
        for value in (
            'metadata.version("fonttools") == "4.65.0"',
            'metadata.version("matplotlib") == "3.11.2"',
            'metadata.version("pandas") == "3.0.6"',
            'metadata.version("tqdm") == "4.70.1"',
            'metadata.version("uvicorn") == "0.53.0"',
            'matplotlib.use("Agg")',
            'findfont("DejaVu Sans", fallback_to_default=False)',
            "TTFont(font_path)",
            'rendered.getvalue().startswith(b"\\x89PNG\\r\\n\\x1a\\n")',
            'converted.getvalue().startswith(b"RIFF")',
            'workbook.active["A1"] = "HolyCode"',
            'Document(document_bytes).paragraphs[0].text == "HolyCode"',
            'list(tqdm(range(3), file=progress, disable=False)) == [0, 1, 2]',
            'uvicorn.run(app, host="127.0.0.1", port=port, log_level="critical")',
            'requests.get(url, timeout=1)',
            'httpx.get(url, timeout=1)',
            'server.start()',
            'server.terminate()',
            'server.join(timeout=5)',
            'server.kill()',
            'assert not server.is_alive()',
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.smoke)

    def test_uvicorn_cleanup_forces_a_stubborn_process_dead(self):
        cleanup = re.search(
            r"def stop_server\(server\):\n(?:    .*\n)+",
            self.smoke,
        )
        self.assertIsNotNone(cleanup)
        namespace = {}
        exec(textwrap.dedent(cleanup.group(0)), namespace)

        class StubbornProcess:
            def __init__(self):
                self.alive = True
                self.events = []

            def terminate(self):
                self.events.append("terminate")

            def join(self, timeout):
                self.events.append(("join", timeout))

            def is_alive(self):
                return self.alive

            def kill(self):
                self.events.append("kill")
                self.alive = False

        server = StubbornProcess()
        namespace["stop_server"](server)
        self.assertEqual(
            server.events,
            ["terminate", ("join", 5), "kill", ("join", 5)],
        )
        self.assertFalse(server.is_alive())

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
        go_builder = (
            "FROM --platform=$BUILDPLATFORM golang:1.27.1-trixie@sha256:"
            "9baa6b4187bbb98d240372a8a235ac0bb6b5ddd52bba1431dc2f7c0705862728"
        )
        self.assertEqual(self.dockerfile.count(go_builder), 3)
        self.assertIn(f"{go_builder} AS github-cli-builder", self.dockerfile)
        self.assertIn("ARG GITHUB_CLI_VERSION=2.101.0", self.dockerfile)
        self.assertIn(
            "ARG GITHUB_CLI_REF=0cf1092493af067646fc5f3db9421c6a6ec9c938",
            self.dockerfile,
        )
        self.assertIn('test "$(git rev-parse HEAD)" = "${GITHUB_CLI_REF}"', self.dockerfile)
        self.assertIn('go version -m /out/gh | grep -F "go1.27.1"', self.dockerfile)
        self.assertIn(
            'test "$(go list -m -f \'{{.Version}}\' google.golang.org/grpc)" = "v1.83.2"',
            self.dockerfile,
        )
        self.assertIn(
            'test "$(go list -m -f \'{{.Version}}\' golang.org/x/mod)" = "v0.41.0"',
            self.dockerfile,
        )
        self.assertNotIn("go get golang.org/x/mod@", self.dockerfile)
        self.assertIn(
            "go version -m /out/gh | grep -E "
            "'github.com/klauspost/compress[[:space:]]+v1\\.20\\.0'",
            self.dockerfile,
        )
        self.assertIn(
            "go version -m /out/gh | grep -E "
            "'golang.org/x/text[[:space:]]+v0\\.42\\.0'",
            self.dockerfile,
        )
        self.assertIn(
            "go version -m /out/gh | grep -E "
            "'golang.org/x/mod[[:space:]]+v0\\.41\\.0'",
            self.dockerfile,
        )
        self.assertNotIn("github-cli-modules.patch", self.dockerfile)
        self.assertIn(
            "FROM node:24.21.0-trixie-slim@sha256:"
            "d7b4e5c4ad20b327d7bb16fab6aecd60ac20aa50f8514eb75a2b059e89abe48e",
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
            "ARG FZF_REF=a140afeb4d733cad3c96a56bf6db7e26853b6757",
            self.dockerfile,
        )
        self.assertIn(
            "ARG LAZYGIT_REF=17cb09fa7b08bc96d9f0e81b91f4720fc1a36700",
            self.dockerfile,
        )
        self.assertIn(
            "go version -m /out/fzf | grep -E "
            "'golang.org/x/sys[[:space:]]+v0\\.44\\.0'",
            self.dockerfile,
        )
        self.assertIn(
            "go version -m /out/lazygit | grep -E "
            "'golang.org/x/text[[:space:]]+v0\\.41\\.0'",
            self.dockerfile,
        )
        self.assertIn(
            "go version -m /out/lazygit | grep -E "
            "'golang.org/x/sys[[:space:]]+v0\\.47\\.0'",
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
        self.assertIn("ARG PIP_VENDOR_MSGPACK_VERSION=1.2.2", self.dockerfile)
        self.assertIn(
            "ARG PIP_VENDOR_MSGPACK_SHA256="
            "9eb0b0e602064527a045ea28c4f174ed69383587e29cebe28947e3b84106eb2a",
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
        self.assertIn("ARG PAPERCLIP_UNDICI_VERSION=6.28.1", self.dockerfile)
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
        self.assertIn("ARG PRISMA_DEEPMERGE_VERSION=8.0.2", self.dockerfile)
        self.assertIn("io.holycode.version.prisma-deepmerge-ts", self.dockerfile)
        self.assertIn("io.holycode.version.prisma-mysql2", self.dockerfile)
        self.assertIn("io.holycode.version.prisma-types-node", self.dockerfile)
        self.assertIn("io.holycode.version.prisma-undici-types", self.dockerfile)
        self.assertIn(
            "sha512-uqbvqLUMrc6p0MO+WBRtTxY55hmyh94WRwI5a++PZe54X+bfVh59FSN7uWCBCW1CCVjzjnrwzfI8zidE2obMMw==",
            self.dockerfile,
        )
        self.assertIn(
            'test "$(npm view "@prisma/config@${PRISMA_VERSION}" dependencies.deepmerge-ts)" = "7.1.5"',
            self.dockerfile,
        )
        self.assertIn("PRISMA_CONFIG_PACKAGE", self.dockerfile)
        self.assertIn('test "$(npm view "prisma@${PRISMA_VERSION}" dependencies.mysql2)" = "3.15.3"', self.dockerfile)
        self.assertIn("sha512-A2olluVlj0mvgyIRRISMEzXc51m+21mRtcMVjJyIpt2GG98+XrC9m9HzsqcMsX2LcnfccJvY5NB22g8fENBnOA==", self.dockerfile)
        self.assertIn(
            'npm install --prefix "$PRISMA_MYSQL2_DIR" --ignore-scripts --package-lock=false --omit=dev',
            self.dockerfile,
        )
        self.assertNotIn('npm install --prefix /usr/local/lib/node_modules/prisma ', self.dockerfile)
        self.assertIn("npm ls deepmerge-ts mysql2 @types/node undici-types --all", self.dockerfile)
        self.assertIn("expected_prisma_deepmerge", self.smoke)
        self.assertIn("EXPECTED_PRISMA_DEEPMERGE", self.smoke)
        self.assertIn("expected_prisma_mysql2", self.smoke)
        self.assertIn("EXPECTED_PRISMA_MYSQL2", self.smoke)
        self.assertIn("expected_prisma_types_node", self.smoke)
        self.assertIn("EXPECTED_PRISMA_TYPES_NODE", self.smoke)
        self.assertIn("expected_prisma_undici_types", self.smoke)
        self.assertIn("EXPECTED_PRISMA_UNDICI_TYPES", self.smoke)
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

    def test_prisma_mysql2_peer_is_raw_integrity_bound_and_graph_checked(self):
        for value in (
            "ARG PRISMA_TYPES_NODE_VERSION=20.19.43",
            "ARG PRISMA_UNDICI_TYPES_VERSION=6.21.0",
            "https://registry.npmjs.org/@types/node/-/node-${PRISMA_TYPES_NODE_VERSION}.tgz",
            "https://registry.npmjs.org/undici-types/-/undici-types-${PRISMA_UNDICI_TYPES_VERSION}.tgz",
            "sha512-6oYBAi5ikg4Pl+kGsoYtawUMBT2zZMCvPNF7pVLnHZfd1zf38DRiWn/gT01RYCdUqkv7Fhr+C9ot4/tb+2sVvA==",
            "sha512-iwDZqg0QAGrg9Rav5H4n0M64c3mkR59cJ6wQp+7C4nI0gsmExaedaYLNO44eT4AtBBwjbTiGPMlt2Md0T9H9JQ==",
            'test ! -e "$PRISMA_TYPES_NODE_DIR"',
            'test ! -e "$PRISMA_UNDICI_TYPES_DIR"',
            'pkg.peerDependencies["@types/node"]!==">= 8"',
            'pkg.peerDependenciesMeta?.["@types/node"]!==undefined',
            'pkg.main!==""',
            'pkg.dependencies["undici-types"]!=="~6.21.0"',
            'test -s "$PRISMA_TYPES_NODE_DIR/index.d.ts"',
            'test -s "$PRISMA_UNDICI_TYPES_DIR/fetch.d.ts"',
            'require.resolve("@types/node/package.json",{paths:[process.argv[1]]})',
            'require.resolve("undici-types/package.json",{paths:[process.argv[1]]})',
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.dockerfile)
        self.assertGreaterEqual(self.dockerfile.count('crypto.createHash("sha512")'), 5)

        for value in (
            "npm ls -g --all --json",
            'test "$npm_tree_status" -eq 1',
            'lighthouse?.version!==\\"13.4.1\\"',
            'trace?.version!==\\"0.0.65\\"',
            'tracePkg.dependencies[\\"third-party-web\\"]!==\\"latest\\"',
            'tracePkg.dependencies[\\"legacy-javascript\\"]!==\\"latest\\"',
            "invalid: third-party-web@0.29.2",
            "invalid: legacy-javascript@0.0.1",
            "missing:",
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.smoke)

        for value in (
            "python3 -m http.server",
            'lighthouse "http://127.0.0.1:',
            '--only-categories=performance',
            '--headless --no-sandbox --disable-gpu --disable-dev-shm-usage',
            'categories.performance.score',
            'kill "$lighthouse_server_pid"',
        ):
            with self.subTest(lighthouse_consumer=value):
                self.assertIn(value, self.smoke)
        for assertion in (
            'assert metadata.version("uvicorn") == "0.53.0"',
            'assert metadata.version("packaging") == "26.3"',
            'assert metadata.version("pip") == "26.2.1"',
            'assert metadata.version("setuptools") == "84.0.0"',
        ):
            with self.subTest(assertion=assertion):
                self.assertIn(assertion, self.smoke)
        self.assertIn("undici@${PAPERCLIP_UNDICI_VERSION}", self.dockerfile)
        self.assertIn(
            "sha512-zWpdTVD54H48CIybL0rWQ3ukpb9d23wM7eH5RtfdmeP70cWHNjtfo7P4vZX+5CoDcO53J4Pu5uXp7lNfjc6DRA==",
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
        self.assertIn("ARG NPM_IP_ADDRESS_VERSION=10.7.2", self.dockerfile)
        self.assertIn(
            "sha512-7H/2gFSIitxc0hG3nOI1glS8QLo/EHBFFLk8vEUjXY/xu0AdL8jZ9U1IzO2PUm0d2D/ofQcAifb0g6OBkt8U7w==",
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

    def test_pm2_js_yaml_security_overlay_is_owner_guarded_and_exercised(self):
        self.assertIn("ARG PM2_JS_YAML_VERSION=4.3.2", self.dockerfile)
        self.assertIn(
            "sha512-SFNOvSJ+Dgf/9An904Yx+CgSlIPCkIpao4qo51lpee25TIRejdH3rhR4EZMGoNx3/TP3O+wzWuiTFl4sqbltzA==",
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
            'npm view pm2@7.0.4 dependencies.js-yaml)" = "4.3.1"',
            self.dockerfile,
        )
        self.assertIn('dependencies["js-yaml"]!=="4.3.1"', self.dockerfile)
        self.assertIn("PM2_JS_YAML_TARBALL", self.dockerfile)
        self.assertIn("PM2_JS_YAML_INTEGRITY", self.dockerfile)
        self.assertIn(
            "npm pack --silent --ignore-scripts --pack-destination /tmp",
            self.dockerfile,
        )
        self.assertIn('"js-yaml@${PM2_JS_YAML_VERSION}")', self.dockerfile)
        self.assertIn(
            '"/tmp/${PM2_JS_YAML_TARBALL}" "$PM2_JS_YAML_INTEGRITY"',
            self.dockerfile,
        )
        self.assertIn('rm -rf "$PM2_JS_YAML_DIR"', self.dockerfile)
        self.assertIn("npm ls js-yaml --all", self.dockerfile)
        self.assertIn('yaml.load("service:\\n  enabled: true\\n")', self.dockerfile)
        self.assertIn("holycode-build-pm2-app.js", self.dockerfile)
        self.assertIn('pm2 start "$PM2_APP"', self.dockerfile)
        self.assertIn("io.holycode.version.pm2-js-yaml", self.dockerfile)
        self.assertNotIn("ARG PM2_JS_YAML_VERSION=4.3.1", self.dockerfile)
        self.assertIn("expected_pm2_js_yaml", self.smoke)
        self.assertIn("EXPECTED_PM2_JS_YAML", self.smoke)
        self.assertIn("npm ls js-yaml --all", self.smoke)
        self.assertIn('yaml.load(\\"service:\\\\n  enabled: true\\\\n\\")', self.smoke)
        self.assertIn("PM2_HOME=/tmp/holycode-smoke-pm2", self.smoke)
        self.assertIn("holycode-smoke-pm2-app.js", self.smoke)
        self.assertIn('pm2 start "$pm2_app"', self.smoke)

    def test_wrangler_miniflare_sharp_is_native_and_owner_guarded_without_overlay(self):
        for value in (
            "ARG WRANGLER_MINIFLARE_VERSION=5.20260917.0-alpha",
            "ARG WRANGLER_SHARP_VERSION=0.35.4",
            "ARG WRANGLER_SHARP_LIBVIPS_VERSION=1.3.3",
            "io.holycode.version.wrangler-miniflare",
            "io.holycode.version.wrangler-sharp",
            "io.holycode.version.wrangler-sharp-libvips",
            "sha512-n++8XWcj+jCOr2IOl7h8LbKnGBDY4aPbmprMONBNFdn0ImXqpGVv5zliDs0V9HbmbCQLpbuo2ej9rAoOQTvMDA==",
            "sha512-9qvvEAuk8k89TfWUoX2htWjbAMX8p+NxCppjpcg5k6xMsjhBQPTsoIh36h9Qde4WRuGpJeYnOjdosDn/cnv+OA==",
            "sha512-De4jpEnAU8Hd5oT0j1G3uL4ZvTuipVMn7YC6vPaJhy6/7EwEae0SVAoBrUMYQbkLGDm85taVWwuPc1a44LTzCQ==",
            "sha512-4vKmvAst9nrowcqquKFAyZJUDolUaIp8uRiN0mWFguJ1IplC9/pitXtlnnlU4aa/eJw3J7i67V+pwUL+wZGdsA==",
            "sha512-0DaL0A6Xu6sQSQFwe4iVCrKWU2cCTItnRsYsCdxAMm9NF6twAA9BKnoqy4hqz4+azQ0JHuA26qiUKsf1XJ/v5A==",
            'npm view "wrangler@${WRANGLER_VERSION}" dependencies.miniflare)" = "${WRANGLER_MINIFLARE_VERSION}"',
            'npm view "wrangler@${WRANGLER_VERSION}" dependencies.workerd)" = "1.20260917.1"',
            'npm view "miniflare@${WRANGLER_MINIFLARE_VERSION}" dependencies.workerd)" = "1.20260917.1"',
            'dependencies.sharp!==process.argv[3]',
            "WRANGLER_SHARP_TARBALL",
            "WRANGLER_SHARP_NATIVE_TARBALL",
            "WRANGLER_SHARP_LIBVIPS_TARBALL",
            "WRANGLER_SHARP_INTEGRITY",
            '"/tmp/${WRANGLER_SHARP_TARBALL}" "$WRANGLER_SHARP_INTEGRITY"',
            '"/tmp/${WRANGLER_SHARP_NATIVE_TARBALL}" "$WRANGLER_SHARP_NATIVE_INTEGRITY"',
            '"/tmp/${WRANGLER_SHARP_LIBVIPS_TARBALL}" "$WRANGLER_SHARP_LIBVIPS_INTEGRITY"',
            "WRANGLER_SHARP_VERIFIED_DIR",
            'diff -qr --no-dereference "$WRANGLER_SHARP_VERIFIED_DIR/package" "$WRANGLER_SHARP_DIR"',
            'diff -qr --no-dereference "$WRANGLER_SHARP_NATIVE_VERIFIED_DIR/package" "$WRANGLER_SHARP_NATIVE_DIR"',
            'diff -qr --no-dereference "$WRANGLER_SHARP_LIBVIPS_VERIFIED_DIR/package" "$WRANGLER_SHARP_LIBVIPS_DIR"',
            "npm ls sharp --all",
            'sharp.versions.sharp!==process.argv[2]',
            'sharp.versions.heif!=="1.23.2"',
            ".avif().toBuffer()",
            ".raw().toBuffer({resolveWithObject:true})",
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.dockerfile)

        self.assertIn('case "${TARGETARCH}" in', self.dockerfile)
        self.assertIn("amd64) WRANGLER_SHARP_ARCH=x64", self.dockerfile)
        self.assertIn("arm64) WRANGLER_SHARP_ARCH=arm64", self.dockerfile)
        self.assertNotIn("ARG WRANGLER_SHARP_VERSION=0.35.2", self.dockerfile)
        self.assertNotIn("ARG WRANGLER_SHARP_LIBVIPS_VERSION=1.3.1", self.dockerfile)
        self.assertEqual(
            self.dockerfile.count("pkg.optionalDependencies[process.argv[3]]"),
            1,
        )
        self.assertNotIn("pkg.dependencies[process.argv[2]]", self.dockerfile)
        self.assertNotIn("ARG WRANGLER_WORKERD_VERSION", self.dockerfile)
        digest_check = (
            'crypto.createHash("sha512").update(fs.readFileSync(process.argv[1]))'
            '.digest("base64")'
        )
        self.assertEqual(self.dockerfile.count(digest_check), 6)
        for obsolete in (
            'rm -rf "$WRANGLER_SHARP_DIR"',
            '-C "$WRANGLER_SHARP_DIR" --strip-components=1',
            'pkg.dependencies.sharp=version',
        ):
            with self.subTest(obsolete=obsolete):
                self.assertNotIn(obsolete, self.dockerfile)

        for value in (
            "expected_wrangler_miniflare",
            "expected_wrangler_sharp",
            "expected_wrangler_sharp_libvips",
            "EXPECTED_WRANGLER_MINIFLARE",
            "EXPECTED_WRANGLER_SHARP",
            "EXPECTED_WRANGLER_SHARP_LIBVIPS",
            "/usr/local/lib/node_modules/wrangler/node_modules/miniflare/package.json",
            "/usr/local/lib/node_modules/wrangler/node_modules/workerd/package.json",
            'pkg.version!==\\"1.20260917.1\\"',
            "workerd_count=0",
            '$(find /usr/local/lib/node_modules -path "*/workerd/package.json" -type f | sort)',
            'test "$workerd_count" -gt 0',
            "wrangler_sharp_dir=/usr/local/lib/node_modules/wrangler/node_modules/sharp",
            "npm ls sharp --all",
            'sharp.versions.sharp!==process.env.EXPECTED_WRANGLER_SHARP',
            'sharp.versions.heif!==\\"1.23.2\\"',
            ".avif().toBuffer()",
            ".raw().toBuffer({resolveWithObject:true})",
            "! command -v sharp",
            "pkg.optionalDependencies[process.argv[2]]",
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.smoke)
        self.assertNotIn("pkg.dependencies[process.argv[2]]", self.smoke)

    def test_all_installed_sharp_copies_and_targeted_wrangler_copy_are_exercised(self):
        for value in (
            "sharp_count=0",
            "while IFS= read -r package_json; do",
            'sharp_dir="${package_json%/package.json}"',
            '$(find /usr/local/lib/node_modules -path "*/sharp/package.json" -type f | sort)',
            'test "$sharp_count" -gt 0',
            "wrangler_sharp_dir=/usr/local/lib/node_modules/wrangler/node_modules/sharp",
            'sharp.versions.sharp!==process.env.EXPECTED_WRANGLER_SHARP',
            'sharp.versions.heif!==\\"1.23.2\\"',
            ".avif().toBuffer()",
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.smoke)

    def test_packed_byte_hashes_precede_package_replacement_and_extraction(self):
        pm2_hash = '"/tmp/${PM2_JS_YAML_TARBALL}" "$PM2_JS_YAML_INTEGRITY"'
        pm2_delete = 'rm -rf "$PM2_JS_YAML_DIR"'
        pm2_extract = 'tar -xzf "/tmp/${PM2_JS_YAML_TARBALL}"'
        self.assertLess(self.dockerfile.index(pm2_hash), self.dockerfile.index(pm2_delete))
        self.assertLess(self.dockerfile.index(pm2_hash), self.dockerfile.index(pm2_extract))

        self.assertNotIn('-C "$WRANGLER_SHARP_DIR" --strip-components=1', self.dockerfile)

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
        self.assertIn("ARG CLAUDE_AUTH_PLUGIN_VERSION=2.2.0", self.dockerfile)
        self.assertNotIn("opencode-claude-auth@2.1.6", self.plugin_modes)
        self.assertIn("opencode-claude-auth@2.2.0", self.plugin_modes)
        self.assertIn(
            "sha512-EYU6hbP9edKQABn5zKMXPdxT5KZLf/0qII7AgahCW2w/FGgJnSE5bbWU5bTGmlHZTAJXixdy94/3WpBgIlHMaA==",
            self.dockerfile,
        )
        self.assertIn('dist.integrity)" =', self.dockerfile)
        self.assertIn("npm pack --silent --pack-destination /tmp", self.dockerfile)
        self.assertIn("/usr/local/share/holycode/plugins/opencode-claude-auth", self.dockerfile)
        self.assertIn('CLAUDE_AUTH_PLUGIN_VERSION="2.2.0"', self.entrypoint)
        self.assertIn("install_offline_claude_auth", self.entrypoint)
        self.assertNotIn('opencode plugin "$plugin_spec" -g -f', self.entrypoint)
        self.assertIn("claude auth status --json", self.smoke)
        self.assertIn(
            '.loggedIn == false and .authMethod == \\"none\\"',
            self.smoke,
        )

    def test_claude_marketplace_smoke_rejects_traversal_and_omits_symlink_targets(self):
        for value in (
            "--read-only",
            "--tmpfs /tmp:rw,exec,nosuid,nodev,mode=1777,size=64m",
            "--cap-drop ALL",
            "--security-opt no-new-privileges",
            "CLAUDE_CONFIG_DIR=/tmp/cc-config",
            'test -z "${ANTHROPIC_API_KEY:-}"',
            "traversal-fixture",
            '"source":"../outside"',
            "claude plugin validate /tmp/fixture/traversal --json",
            'grep -F "Path contains"',
            "SAFE_MARKER_2_1_268",
            "OUTSIDE_MARKER_2_1_268",
            'readlink -f "$plugin_dir/leak-dir"',
            "claude plugin marketplace add /tmp/fixture/market",
            "claude plugin install escape-plugin@containment-fixture --scope user",
            "plugins/cache/containment-fixture/escape-plugin/1.0.0",
            'test ! -e "$claude_plugin_cache/leak-dir"',
            'test ! -L "$claude_plugin_cache/leak-dir"',
            'if grep -R -F "OUTSIDE_MARKER_2_1_268" "$claude_plugin_cache"',
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.smoke)

        audit = self.dependency_audit.read_text(encoding="utf-8")
        self.assertIn(
            "synthetic-auth startup and marketplace/path-containment regression coverage are required release gates through `scripts/smoke_image.sh`",
            audit,
        )
        self.assertNotIn("remains pending a separate fixture investigation", audit)
        self.assertIn("no live account, provider, OAuth, or billing claim", audit)

    def test_oh_my_openagent_managed_install_is_suspended(self):
        self.assertNotIn("OH_MY_OPENAGENT_PLUGIN_VERSION", self.entrypoint)
        self.assertNotIn("ensure_plugin_installed \"$OH_MY_OPENAGENT_PLUGIN_NAME\"", self.entrypoint)
        self.assertNotIn("plugin_spec_from_config", self.entrypoint)
        self.assertIn(
            'migrate_oh_my_openagent_config "$CONFIG_FILE"',
            self.entrypoint,
        )
        self.assertIn(
            "HolyCode-managed oh-my-openagent installation is currently unavailable.",
            self.entrypoint,
        )
        self.assertNotIn(
            "HolyCode-managed oh-my-openagent installation is unavailable in v1.1.4.",
            self.entrypoint,
        )
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
        self.assertIn(
            "The bundled Hermes is temporarily unavailable.",
            self.entrypoint,
        )
        self.assertIn("bundled Hermes is temporarily unavailable", self.entrypoint)
        self.assertNotIn(
            "The bundled Hermes is temporarily unavailable in v1.1.4",
            self.entrypoint,
        )
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

    def test_v1_2_2_uses_v1_2_1_as_its_git_predecessor(self):
        self.assertIn("RELEASE_VERSION: v1.2.2", self.protected)
        self.assertIn("PREVIOUS_VERSION: v1.2.1", self.protected)
        self.assertIn(
            "coderluii/holycode:1.2.1@sha256:12382641397dd477fe4a57a7dcf74107b05062c5285f0f50cc8664056701a2b2",
            self.protected,
        )
        self.assertIn("needs: protected-validation", self.publish)
        self.assertNotIn("./.github/workflows/protected-validation.yml", self.publish)
        self.assertIn("Download protected candidate digest", self.publish)
        self.assertNotIn("event=workflow_dispatch", self.publish)
        self.assertEqual(self.publish.count("docker/build-push-action"), 1)
        self.assertNotIn("config/security-exceptions-v1.1.4.json", self.protected)

    def test_v1_2_2_release_metadata_is_documented(self):
        self.assertRegex(self.changelog, r"(?m)^## \[1\.2\.2\] - 09/18/2026$")
        self.assertTrue(self.dependency_audit.is_file())
        audit = self.dependency_audit.read_text(encoding="utf-8")
        self.assertIn("Git predecessor `v1.2.1`", audit)
        self.assertIn(
            "`coderluii/holycode:1.2.1@sha256:12382641397dd477fe4a57a7dcf74107b05062c5285f0f50cc8664056701a2b2`",
            audit,
        )
        self.assertTrue((ROOT / "docs" / "dependency-audit-v1.1.9.md").is_file())
        self.assertTrue((ROOT / "docs" / "dependency-audit-v1.2.0.md").is_file())
        self.assertTrue((ROOT / "docs" / "dependency-audit-v1.2.1.md").is_file())
        self.assertIn("v1.2.2 release pins", self.readme)
        self.assertIn("dependency-audit-v1.2.2.md", self.readme)
        self.assertIn("v1.2.2", self.dockerhub)
        for document in (self.readme, self.dockerhub):
            with self.subTest(document="current release copy"):
                self.assertIn("@anthropic-ai/claude-code@2.1.276", document)
                self.assertNotIn("@anthropic-ai/claude-code@2.1.270", document)
        self.assertIn("Python 3.13.15", audit)
        self.assertIn("pip 26.2.1", audit)
        self.assertIn("pip-tools 7.6.1", audit)
        self.assertIn("Click 8.4.2", audit)
        self.assertIn("Product `click==8.5.0`", audit)
        self.assertIn("Automatic pip-tools lock updates are therefore still blocked", audit)
        self.assertIn("native ARM64", audit)
        self.assertIn("`opencode-claude-auth 2.2.0`", audit)
        for value in (
            "| Paperclip | 2026.831.1 | 2026.916.0 |",
            "supported narrow self-hosted control preserves explicit user choices",
            "| TypeScript | 6.0.3 | 7.0.2 |",
            "| Prisma | 7.10.0 | 8.0.0-rc.15 |",
            "| json-server | 0.17.4 | 1.0.0-beta.15 |",
            "| PM2-owned js-yaml | 4.3.2 | 5.4.2 |",
            "| Paperclip-owned Undici | 6.28.1 | 8.10.2 |",
            "Drizzle ORM 0.45.2 is already a Paperclip transitive",
            "16 local entries with 27 verified local files",
            "one optional pinned remote descriptor with 79 metadata records",
            "does not claim the release has shipped",
        ):
            with self.subTest(dependency_hold=value):
                self.assertIn(value, audit)
        self.assertIn("js-yaml 4.3.2", self.notices)
        self.assertIn("brace-expansion 5.0.12", self.notices)
        self.assertIn("ip-address 10.7.2", self.notices)
        for value in (
            "@types/node 20.19.43",
            "undici-types 6.21.0",
            "type-only peer",
        ):
            with self.subTest(prisma_peer_notice=value):
                self.assertIn(value, self.notices)
        for value in (
            "@types/node 20.19.43",
            "undici-types 6.21.0",
            "Lighthouse 13.4.1",
            "@paulirish/trace_engine 0.0.65",
            "third-party-web 0.29.2",
            "legacy-javascript 0.0.1",
            "not a universal clean-tree claim",
        ):
            with self.subTest(prisma_peer_audit=value):
                self.assertIn(value, audit)
        for value in (
            "@anthropic-ai/claude-code@2.1.276",
            "0.65.1 (`17cb09fa7b08bc96d9f0e81b91f4720fc1a36700`)",
            "Wrangler owns Miniflare 5.20260917.0-alpha and workerd 1.20260917.1",
            "0.74.4 (`a140afeb4d733cad3c96a56bf6db7e26853b6757`)",
            "2.101.0 (`0cf1092493af067646fc5f3db9421c6a6ec9c938`)",
            "Playwright",
            "Version: 1.63.0",
            "pandas",
            "Version: 3.0.6",
        ):
            with self.subTest(notice=value):
                self.assertIn(value, self.notices)

    def test_current_translation_summaries_match_v1_2_2(self):
        for path in sorted((ROOT / "docs" / "translations").glob("README.*.md")):
            translation = path.read_text(encoding="utf-8")
            with self.subTest(translation=path.name):
                for value in (
                    "v1.2.2",
                    "OpenCode 1.18.31",
                    "OpenSpec 1.13.1",
                    "Claude Code 2.1.276",
                    "pnpm 12.4.2",
                    "Prettier 3.9.8",
                    "Wrangler 4.134.0",
                    "Miniflare 5.20260917.0-alpha",
                    "workerd 1.20260917.1",
                    "Playwright 1.63.0",
                    "pandas 3.0.6",
                    "Matplotlib 3.11.2",
                    "tqdm 4.70.1",
                    "Uvicorn 0.53.0",
                    "`1.2.1`",
                ):
                    self.assertIn(value, translation)

    def test_release_apt_refresh_matches_preparation_date(self):
        self.assertIn("ARG RELEASE_APT_REFRESH=2026-09-18", self.dockerfile)

    def test_openspec_is_pinned_installed_and_telemetry_disabled(self):
        self.assertIn(
            "# renovate: datasource=npm depName=@fission-ai/openspec\n"
            "ARG OPENSPEC_VERSION=1.13.1",
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
        self.assertIn('openspec_bind_source="$openspec_workspace"', self.smoke)
        self.assertIn("if command -v cygpath >/dev/null 2>&1; then", self.smoke)
        self.assertIn(
            'openspec_bind_source="$(cygpath -w "$openspec_workspace")"',
            self.smoke,
        )
        self.assertEqual(
            self.smoke.count('-v "$openspec_bind_source:/workspace"'),
            2,
        )
        self.assertNotIn('-v "$openspec_workspace:/workspace"', self.smoke)
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
        for value in (
            "openspec new change holycode-smoke",
            "openspec instructions apply --change holycode-smoke --json",
            'jq -e ".state == \\"ready\\""',
            "openspec validate holycode-smoke --strict",
            "openspec archive holycode-smoke --yes --json",
            "openspec/specs/holycode-smoke/spec.md",
            "openspec/changes/archive/",
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.smoke)

    def test_vite_smoke_builds_and_serves_a_local_fixture(self):
        for value in (
            'vite_workspace="$(mktemp -d)"',
            'vite build "$vite_workspace"',
            'vite preview "$vite_workspace"',
            "--strictPort",
            'curl -fsS "http://127.0.0.1:$vite_port/"',
            "HolyCode Vite smoke",
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.smoke)

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

    def test_upgrade_fixture_covers_paperclip_2026_831_migrations(self):
        self.assertIn('[ "$current_paperclip_version" = "2026.831.1" ]', self.upgrade)
        self.assertIn("paperclip_2026_831_migration=false", self.upgrade)
        self.assertRegex(
            self.upgrade,
            r'previous_paperclip_version" = "2026\.824\.1"[\s\S]*?'
            r"paperclip_2026_831_migration=true",
        )
        self.assertIn('insert into "account"', self.upgrade)
        self.assertIn("holycode-credential-account", self.upgrade)
        self.assertIn("holycode-oauth-account", self.upgrade)
        self.assertIn("local:credential", self.upgrade)
        self.assertIn("local:oauth:holycode-oauth", self.upgrade)
        self.assertIn("insert into adapter_auth_sessions", self.upgrade)
        self.assertIn("insert into claude_setup_token_sessions", self.upgrade)

        for filename in (
            "0223_robust_zaladane.sql",
            "0224_unified_adapter_auth_sessions.sql",
            "0225_drop_claude_setup_token_sessions.sql",
            "0226_tan_colossus.sql",
            "0227_modern_pandemic.sql",
            "0228_nasty_grim_reaper.sql",
            "0229_drop_company_brand_color_and_attachment_max_bytes.sql",
            "0230_better_auth_account_issuer.sql",
        ):
            with self.subTest(filename=filename):
                self.assertIn(filename, self.upgrade)

        for assertion in (
            "adapter auth sessions reset by migration 0224",
            "adapter_auth_sessions_public_session_id_uq",
            "adapter_auth_sessions_company_owner_adapter_active_uq",
            "claude setup token table removed by migration 0225",
            "company attachment_max_bytes removed by migration 0229",
            "company brand_color removed by migration 0229",
            "credential account issuer backfilled by migration 0230",
            "OAuth account issuer backfilled by migration 0230",
            "account_issuer_account_id_uq",
        ):
            with self.subTest(assertion=assertion):
                self.assertIn(assertion, self.upgrade)

    def test_paperclip_packaged_skill_catalog_is_exercised_without_user_skill_writes(self):
        for value in (
            "paperclip_catalog=/usr/local/lib/node_modules/paperclipai/node_modules/@paperclipai/skills-catalog/generated/catalog.json",
            'catalog.packageName !== "@paperclipai/skills-catalog"',
            "catalog.schemaVersion !== 1",
            "catalog.skills.length === 0",
            'allowedTrustLevels = new Set(["markdown_only", "assets", "scripts_executables"])',
            "skill.trustLevel !== derivedTrustLevel",
            'skill.id !== "paperclipai:optional:research:last30days"',
            'resolve(lexicalSkillRoot, "catalog-ref.json")',
            "descriptor.source?.[key] !== source[key]",
            "localSkills !== 16 || remoteSkills !== 1 || localFiles !== 27 || remoteFiles !== 79",
            "remoteFiles += 1",
            "remote.files.length !== 79",
            "remote.files = remote.files.slice(0, -1)",
            "truncated remote catalog metadata was accepted",
            "file.sizeBytes <= 0",
            "statSync(filePath).size !== file.sizeBytes",
            "realpathSync",
            "isSymbolicLink()",
            'createHash("sha256").update(readFileSync(filePath)).digest("hex") !== file.sha256',
            "npm ls @paperclipai/skills-catalog --all",
            "catalog symlink escape was accepted",
            "ln -s /etc/passwd",
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.smoke)
        self.assertNotIn("tracked17skillpayload", self.smoke)
        self.assertNotIn("/home/opencode/.config/opencode/skills", self.smoke)

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
            "bash scripts/validate_renovate_extraction.sh 44.97.6",
            self.pr_validation,
        )
        self.assertIn(
            "bash scripts/validate_renovate_extraction.sh 44.97.6",
            self.protected,
        )
        self.assertIn(
            "bash scripts/validate_renovate_extraction.sh 44.97.6",
            self.workflow_pin_validator,
        )
        self.assertIn(
            'renovate_version="${1:-44.97.6}"',
            self.renovate_extraction,
        )
        for pin in (
            "docker/setup-qemu-action@99012661954931238ded8c8b007157a8430204e1 # v4.4.0",
            "docker/setup-buildx-action@f87e5991a6d7451dcb8d9637bfbc97413f497069 # v4.4.1",
            "docker/build-push-action@c3c9e263c25d99ce0380d002d59b67737d91b0dc # v7.4.0",
        ):
            with self.subTest(pin=pin):
                self.assertIn(pin, self.publish)
        setup_node = (
            "actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0"
        )
        self.assertIn(setup_node, self.pr_validation)
        self.assertIn(setup_node, self.protected)
        self.assertIn("node-version: 24.21.0", self.pr_validation)
        self.assertIn("node-version: 24.21.0", self.protected)
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

    def test_typescript_and_pnpm_runtime_contracts_are_exercised(self):
        self.assertIn("ARG TYPESCRIPT_VERSION=6.0.3", self.dockerfile)
        self.assertIn('command -v tsserver', self.smoke)
        self.assertIn(r"const value: string = \047holycode\047;", self.smoke)
        self.assertIn("tsc --strict --noEmit", self.smoke)
        self.assertIn(
            'require("/usr/local/lib/node_modules/typescript/lib/typescript.js")',
            self.smoke,
        )
        self.assertIn("ts.createProgram", self.smoke)
        self.assertIn("pnpm install --offline --ignore-scripts", self.smoke)
        self.assertIn("pnpm-lock.yaml", self.smoke)
        self.assertIn("pnpm run verify", self.smoke)

    def test_non_python_runtime_behavior_contracts_are_exercised(self):
        for value in (
            'printf "alpha\\nneedle-result\\nomega\\n" | fzf --filter=needle',
            "expected_lazygit",
            "lazygit --path $lazygit_repo",
            "TSServer protocol smoke passed",
            "npm install --offline --ignore-scripts",
            "eslint --config",
            "prettier --write",
            "prisma db push --schema ./schema.prisma --url file:./smoke.db",
            "wrangler dev --local --ip 127.0.0.1",
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.smoke)

        main_smoke = self.smoke.split('openspec_workspace="$(mktemp -d)"', 1)[0]
        self.assertIn(
            'docker run --rm -i --network none --security-opt',
            main_smoke,
        )
        wrangler_loopback = main_smoke[main_smoke.index("  (\n    cd /tmp/wrangler-modern") :]
        self.assertIn("wrangler dev --local --ip 127.0.0.1", wrangler_loopback)
        self.assertIn("curl -fsS http://127.0.0.1:8787/", wrangler_loopback)
        self.assertIn('test "$wrangler_ready" = true', wrangler_loopback)
        self.assertIn('kill "$wrangler_pid"', wrangler_loopback)
        self.assertIn('wait "$wrangler_pid" || true', wrangler_loopback)
        self.assertNotIn("0.0.0.0", wrangler_loopback)

    def test_main_smoke_script_is_streamed_over_stdin(self):
        main_smoke = self.smoke.split('openspec_workspace="$(mktemp -d)"', 1)[0]
        self.assertIn(
            'docker run --rm -i --network none --security-opt',
            main_smoke,
        )
        self.assertIn("$image\" -lc 'exec sh -eu -s' <<'HOLYCODE_SMOKE'", main_smoke)
        self.assertIn("\nHOLYCODE_SMOKE\n", main_smoke)
        self.assertNotIn("$image\" -lc '\n", main_smoke)
        for guarded_probe in (
            "prisma db push --schema ./schema.prisma --url file:./smoke.db",
            "lighthouse --version",
        ):
            with self.subTest(guarded_probe=guarded_probe):
                self.assertIn(guarded_probe, main_smoke)

    def test_drizzle_behavior_fixture_is_exact_and_network_isolated(self):
        fixture = ROOT / "tests" / "fixtures" / "drizzle-smoke"
        package_json = fixture / "package.json"
        package_lock = fixture / "package-lock.json"
        schema = fixture / "schema.ts"
        for path in (package_json, package_lock, schema):
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file())

        manifest = json.loads(package_json.read_text(encoding="utf-8"))
        lock = json.loads(package_lock.read_text(encoding="utf-8"))
        self.assertEqual(manifest["dependencies"], {"drizzle-orm": "0.45.2"})
        self.assertEqual(
            lock["packages"]["node_modules/drizzle-orm"]["integrity"],
            "sha512-kY0BSaTNYWnoDMVoyY8uxmyHjpJW1geOmBMdSSicKo9CIIWkSxMIj2rkeSR51b8KAPB7m+qysjuHme5nKP+E5Q==",
        )
        drizzle_setup, drizzle_offline = self.smoke.split(
            "docker run --rm --network none --entrypoint sh \\\n"
            '  --mount "type=volume,src=$drizzle_volume,dst=/fixture"',
            1,
        )
        drizzle_setup = drizzle_setup[drizzle_setup.index("drizzle_fixture_dir=") :]
        self.assertIn("docker run --rm -i --entrypoint sh", drizzle_setup)
        self.assertNotIn("--network none", drizzle_setup)
        self.assertIn("npm ci --ignore-scripts --omit=optional --omit=peer", drizzle_setup)
        for setting in (
            "--fetch-retries=2",
            "--fetch-retry-mintimeout=1000",
            "--fetch-retry-maxtimeout=10000",
            "--fetch-timeout=30000",
        ):
            with self.subTest(setting=setting):
                self.assertIn(setting, drizzle_setup)
                self.assertNotIn(setting, drizzle_offline)

        self.assertIn('drizzle-kit generate --dialect sqlite', drizzle_offline)
        self.assertIn("test ! -e node_modules/.bin/drizzle-kit", drizzle_offline)
        self.assertIn("ln -s /fixture/node_modules/drizzle-orm", drizzle_offline)
        self.assertIn(
            'grep -F "CREATE TABLE \\`smoke\\`" "$drizzle_sql"',
            drizzle_offline,
        )

    def test_lazygit_runtime_version_is_bound_to_its_existing_arg(self):
        self.assertIn("io.holycode.version.lazygit=${LAZYGIT_VERSION}", self.dockerfile)
        self.assertIn("EXPECTED_LAZYGIT", self.smoke)

    def test_runtime_python_stack_is_exercised(self):
        for value in (
            "import numpy as np",
            "pd.Series",
            "etree.fromstring",
            "TestClient",
            "response_model=Health",
            "response.status_code == 200",
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.smoke)

    def test_third_party_license_files_are_bundled_and_exercised(self):
        self.assertIn(
            "COPY THIRD-PARTY-NOTICES /usr/local/share/holycode/THIRD-PARTY-NOTICES",
            self.dockerfile,
        )
        for path in (
            "/usr/local/share/holycode/THIRD-PARTY-NOTICES",
            "/usr/local/lib/node_modules/@anthropic-ai/claude-code/LICENSE.md",
            "/usr/local/lib/node_modules/pm2/GNU-AGPL-3.0.txt",
        ):
            with self.subTest(path=path):
                self.assertIn(f'test -r {path} && test -s {path}', self.smoke)

    def test_lifecycle_policy_matches_release(self):
        policy = json.loads((ROOT / "config" / "npm-global-script-policy.json").read_text(encoding="utf-8"))
        self.assertEqual(policy["npmVersion"], "12.0.2")
        self.assertEqual(
            policy["allowScripts"]["@anthropic-ai/claude-code@2.1.276"]["integrity"],
            "sha512-xgVXCbFdqOhSAcMTSC61gjL1jCQuoAA4TNU1I7Dmf/yuYcDxHf796r6LaB3Jswm1floKnP1V+/zfphtDlPdlkg==",
        )
        self.assertEqual(
            policy["allowScripts"]["@anthropic-ai/claude-code@2.1.276"]["scripts"],
            {"postinstall": "node install.cjs"},
        )
        self.assertEqual(
            policy["allowScripts"]["opencode-ai@1.18.31"]["integrity"],
            "sha512-J95feefeWwtIaw3irx76WjzWcgQXxmuHmDVphvs5ep9X30fBJ6T6bFhw50i9Kx50MG/xPn5w2pafXIfNtdry9w==",
        )
        self.assertEqual(
            policy["blockedScripts"]["esbuild@0.28.1"]["integrity"],
            "sha512-HrJrvZv5ayxBzPfwphOoNzkzOIIlifzk0KJrGK2c8R4+LKpMtpYLQeUdjnwjWv/LZlkH2laZk+4w78pi99D4Vw==",
        )
        self.assertIn("Wrangler 4.134.0", policy["blockedScripts"]["esbuild@0.28.1"]["reason"])
        self.assertIn("esbuild@0.28.2", policy["blockedScripts"])
        self.assertEqual(
            policy["blockedScripts"]["workerd@1.20260917.1"]["integrity"],
            "sha512-k072RxsZfRz2cnyAq1Titt+0VpNfnFizSXUkT3r15CDJECBfBXj6JeKK0Bk5CrBLAHGP+dvOHjI//TP7GHXDEw==",
        )
        self.assertEqual(
            policy["blockedScripts"]["pnpm@12.4.2"]["scripts"],
            {"preinstall": "node install.js", "postinstall": "node install.js"},
        )
        self.assertEqual(
            policy["blockedScripts"]["pnpm@12.4.2"]["integrity"],
            "sha512-CK3GYTGAJ1x8ntraOdzwjJxhrU5+rzMKTzRh8QKw+QdCNFTRF/mOctR/7wYWBwZE17/8lzpqV/UJCm18NosHyQ==",
        )
        self.assertIn("prisma@7.10.0", policy["blockedScripts"])
        self.assertIn("@prisma/engines@7.10.0", policy["blockedScripts"])
        self.assertNotIn("netlify-cli@26.2.0", policy["blockedScripts"])
        for decision in ("allowScripts", "blockedScripts"):
            for package_id, entry in policy[decision].items():
                with self.subTest(package_id=package_id):
                    self.assertRegex(entry["integrity"], r"^sha512-")
                    self.assertTrue(entry["architectures"])

    def test_python_lock_header_is_renovate_pip_compile_compatible(self):
        for lock_name, lock in (
            ("python-requirements", self.python_lock),
            ("python-seed-requirements", self.python_seed_lock),
        ):
            header = "\n".join(lock.splitlines()[:8])
            with self.subTest(lock=lock_name):
                for value in (
                    "Python 3.13",
                    "pip-compile",
                    "--allow-unsafe",
                    "--generate-hashes",
                    "--strip-extras",
                    "--index-url=https://pypi.org/simple",
                    "--no-emit-index-url",
                    f"--output-file=config/{lock_name}.lock",
                    f"config/{lock_name}.in",
                ):
                    self.assertIn(value, header)
                self.assertNotIn("--no-index", header)
                self.assertNotIn("--reuse-hashes", header)
                self.assertNotIn("pip-compile --upgrade", header)


if __name__ == "__main__":
    unittest.main()
