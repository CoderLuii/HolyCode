import json
import io
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import contextmanager
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "scripts" / "entrypoint.sh"


class CLIProxyAPIProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        entrypoint = ENTRYPOINT.read_text(encoding="utf-8")
        start = entrypoint.index("import hashlib\n", entrypoint.index("# CLIProxyAPI provider"))
        end = entrypoint.index("\nPY\n", start)
        cls.provider_script = entrypoint[start:end]

    def run_provider(
        self,
        config,
        *,
        enabled="true",
        models="",
        model="",
        small_model="",
        api_key_is_set=False,
        api_key_value=None,
        base_url="http://proxy.test:8317/v1",
        marker=None,
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / "opencode.json"
            marker_file = temp_path / ".holycode-cliproxyapi-provider.sha256"
            config_file.write_text(json.dumps(config), encoding="utf-8")
            if marker is not None:
                marker_file.write_text(marker, encoding="utf-8")

            env = os.environ.copy()
            if api_key_value is None:
                env.pop("CLIPROXYAPI_API_KEY", None)
            else:
                env["CLIPROXYAPI_API_KEY"] = api_key_value

            result = subprocess.run(
                [
                    sys.executable,
                    "-",
                    str(config_file),
                    str(marker_file),
                    enabled,
                    base_url,
                    models,
                    model,
                    small_model,
                    "set" if api_key_is_set else "",
                ],
                input=self.provider_script,
                text=True,
                capture_output=True,
                check=True,
                env=env,
            )
            updated = json.loads(config_file.read_text(encoding="utf-8"))
            updated_marker = marker_file.read_text(encoding="utf-8") if marker_file.exists() else None
            return updated, updated_marker, result.stdout

    @contextmanager
    def models_endpoint(self, response_body, *, status=200, chunk_delay=0):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append((self.path, self.headers.get("Authorization")))
                body = response_body.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                try:
                    if chunk_delay:
                        for byte in body:
                            self.wfile.write(bytes([byte]))
                            self.wfile.flush()
                            time.sleep(chunk_delay)
                    else:
                        self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, format, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.daemon_threads = True
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/v1", requests
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def run_provider_in_process(self, *, models):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / "opencode.json"
            marker_file = temp_path / ".holycode-cliproxyapi-provider.sha256"
            config_file.write_text("{}", encoding="utf-8")
            original_argv = sys.argv
            sys.argv = [
                "-",
                str(config_file),
                str(marker_file),
                "true",
                "http://proxy.test:8317/v1",
                models,
                "",
                "",
                "",
            ]
            output = io.StringIO()
            try:
                started = time.monotonic()
                with redirect_stdout(output):
                    exec(compile(self.provider_script, "<cliproxyapi-provider>", "exec"), {})
                elapsed = time.monotonic() - started
            finally:
                sys.argv = original_argv
            updated = json.loads(config_file.read_text(encoding="utf-8"))
            return updated, elapsed

    def test_discovers_all_endpoint_models_when_explicit_models_are_empty(self):
        body = json.dumps(
            {
                "object": "list",
                "data": [
                    {"id": "model-a", "object": "model"},
                    {"id": "vendor/model-b", "object": "model"},
                    {"id": "model-a", "object": "model"},
                ],
            }
        )
        with self.models_endpoint(body) as (base_url, requests):
            updated, marker, output = self.run_provider(
                {},
                base_url=base_url,
                api_key_is_set=True,
                api_key_value="test-provider-key",
            )

        self.assertEqual(
            list(updated["provider"]["cliproxyapi"]["models"]),
            ["model-a", "vendor/model-b"],
        )
        self.assertIsNotNone(marker)
        self.assertEqual(requests, [("/v1/models", "Bearer test-provider-key")])
        self.assertIn("discovered 2 model(s)", output)
        self.assertNotIn("test-provider-key", output)

    def test_slow_drip_response_stops_at_total_discovery_deadline(self):
        body = json.dumps({"data": [{"id": "slow-model"}]})
        with self.models_endpoint(body, chunk_delay=0.2) as (base_url, _):
            started = time.monotonic()
            updated, marker, output = self.run_provider({}, base_url=base_url)
            elapsed = time.monotonic() - started

        self.assertEqual(updated, {})
        self.assertIsNone(marker)
        self.assertLess(elapsed, 5.8)
        self.assertIn("model discovery failed (deadline exceeded)", output)

    def test_explicit_model_deduplication_is_linear_for_large_lists(self):
        models = ",".join(f"model-{index:05d}" for index in range(40000))

        updated, elapsed = self.run_provider_in_process(models=models)

        self.assertEqual(len(updated["provider"]["cliproxyapi"]["models"]), 40000)
        self.assertLess(elapsed, 2.0)

    def test_discovered_model_deduplication_is_linear_for_large_lists(self):
        body = json.dumps(
            {"data": [{"id": f"m{index:05d}"} for index in range(40000)]},
            separators=(",", ":"),
        )
        with self.models_endpoint(body) as (base_url, _):
            started = time.monotonic()
            updated, _, _ = self.run_provider({}, base_url=base_url)
            elapsed = time.monotonic() - started

        self.assertEqual(len(updated["provider"]["cliproxyapi"]["models"]), 40000)
        self.assertLess(elapsed, 3.0)

    def test_unexpected_worker_error_is_reraised_promptly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / "opencode.json"
            marker_file = temp_path / ".holycode-cliproxyapi-provider.sha256"
            config_file.write_text("{}", encoding="utf-8")
            script = """\
import urllib.request

def fail_build_opener(*args, **kwargs):
    raise RuntimeError('synthetic discovery worker failure')

urllib.request.build_opener = fail_build_opener
""" + self.provider_script

            started = time.monotonic()
            result = subprocess.run(
                [
                    sys.executable,
                    "-",
                    str(config_file),
                    str(marker_file),
                    "true",
                    "http://127.0.0.1:1/v1",
                    "",
                    "",
                    "",
                    "",
                ],
                input=script,
                text=True,
                capture_output=True,
                check=False,
            )
            elapsed = time.monotonic() - started

        self.assertNotEqual(result.returncode, 0)
        self.assertLess(elapsed, 2.0)
        self.assertIn("RuntimeError: synthetic discovery worker failure", result.stderr)
        self.assertNotIn("deadline exceeded", result.stdout)

    def test_explicit_model_list_exposes_multiple_models(self):
        updated, marker, output = self.run_provider(
            {"$schema": "https://opencode.ai/config.json"},
            models=" gpt-5.2 , claude/sonnet ,gpt-5.2, gemini-2.5-pro ",
        )

        provider = updated["provider"]["cliproxyapi"]
        self.assertEqual(
            list(provider["models"]),
            ["gpt-5.2", "claude/sonnet", "gemini-2.5-pro"],
        )
        self.assertEqual(
            provider["models"]["claude/sonnet"],
            {"name": "claude/sonnet via CLIProxyAPI"},
        )
        self.assertIsNotNone(marker)
        self.assertIn("CLIProxyAPI provider enabled with 3 model(s)", output)

    def test_legacy_primary_and_small_models_remain_supported(self):
        updated, _, _ = self.run_provider(
            {}, model="primary-model", small_model="small-model"
        )

        self.assertEqual(
            list(updated["provider"]["cliproxyapi"]["models"]),
            ["primary-model", "small-model"],
        )

    def test_explicit_and_legacy_models_are_merged_without_duplicates(self):
        updated, _, _ = self.run_provider(
            {},
            models="model-a,model-b",
            model="model-b",
            small_model="model-c",
        )

        self.assertEqual(
            list(updated["provider"]["cliproxyapi"]["models"]),
            ["model-a", "model-b", "model-c"],
        )

    def test_enabled_provider_without_models_is_not_added(self):
        original = {"$schema": "https://opencode.ai/config.json", "plugin": ["example"]}
        updated, marker, output = self.run_provider(
            original, base_url="http://127.0.0.1:1/v1"
        )

        self.assertEqual(updated, original)
        self.assertIsNone(marker)
        self.assertIn(
            "CLIProxyAPI model discovery failed (network error); "
            "set CLIPROXYAPI_MODELS or CLIPROXYAPI_MODEL",
            output,
        )

    def test_malformed_discovery_response_does_not_add_provider(self):
        with self.models_endpoint('{"data":"not-a-list"}') as (base_url, _):
            updated, marker, output = self.run_provider({}, base_url=base_url)

        self.assertEqual(updated, {})
        self.assertIsNone(marker)
        self.assertIn("model discovery failed (invalid response)", output)

    def test_discovery_failure_does_not_log_api_key(self):
        with self.models_endpoint('{"error":"unauthorized"}', status=401) as (
            base_url,
            requests,
        ):
            updated, marker, output = self.run_provider(
                {},
                base_url=base_url,
                api_key_is_set=True,
                api_key_value="test-provider-key",
            )

        self.assertEqual(updated, {})
        self.assertIsNone(marker)
        self.assertEqual(requests, [("/v1/models", "Bearer test-provider-key")])
        self.assertIn("model discovery failed (HTTP 401)", output)
        self.assertNotIn("test-provider-key", output)

    def test_api_key_is_stored_only_as_an_environment_reference(self):
        updated, _, output = self.run_provider(
            {}, models="model-a", api_key_is_set=True
        )

        serialized = json.dumps(updated)
        self.assertEqual(
            updated["provider"]["cliproxyapi"]["options"]["apiKey"],
            "{env:CLIPROXYAPI_API_KEY}",
        )
        self.assertNotIn("CLIPROXYAPI_API_KEY=", serialized)
        self.assertNotIn("apiKey", output)

    def test_user_owned_provider_is_preserved(self):
        original = {
            "provider": {
                "cliproxyapi": {
                    "npm": "@ai-sdk/openai-compatible",
                    "name": "User provider",
                    "models": {"user-model": {}},
                }
            }
        }
        updated, marker, output = self.run_provider(original, models="managed-model")

        self.assertEqual(updated, original)
        self.assertIsNone(marker)
        self.assertIn("preserving user config", output)

    def test_empty_explicit_models_preserve_user_owned_provider_without_discovery(self):
        original = {
            "provider": {
                "cliproxyapi": {
                    "npm": "@ai-sdk/openai-compatible",
                    "name": "User provider",
                    "models": {"user-model": {}},
                }
            }
        }
        updated, marker, output = self.run_provider(
            original, base_url="http://127.0.0.1:1/v1"
        )

        self.assertEqual(updated, original)
        self.assertIsNone(marker)
        self.assertIn("preserving user config", output)
        self.assertNotIn("model discovery failed", output)

    def test_managed_provider_updates_on_restart(self):
        first, marker, _ = self.run_provider({}, models="model-a")
        updated, updated_marker, _ = self.run_provider(
            first, models="model-b,model-c", marker=marker
        )

        self.assertEqual(
            list(updated["provider"]["cliproxyapi"]["models"]),
            ["model-b", "model-c"],
        )
        self.assertNotEqual(updated_marker, marker)

    def test_discovery_failure_preserves_last_managed_provider(self):
        first, marker, _ = self.run_provider(
            {"plugin": ["example"]}, models="model-a"
        )
        updated, updated_marker, output = self.run_provider(
            first, marker=marker, base_url="http://127.0.0.1:1/v1"
        )

        self.assertEqual(updated, first)
        self.assertEqual(updated_marker, marker)
        self.assertIn("model discovery failed (network error)", output)
        self.assertIn("Preserving the last HolyCode-managed", output)

    def test_disabling_managed_provider_removes_only_that_provider(self):
        first, marker, _ = self.run_provider(
            {
                "plugin": ["opencode-claude-auth@2.2.0"],
                "provider": {"anthropic": {"options": {"timeout": 120000}}},
            },
            models="model-a",
        )
        updated, updated_marker, output = self.run_provider(
            first, enabled="false", marker=marker
        )

        self.assertEqual(
            updated,
            {
                "plugin": ["opencode-claude-auth@2.2.0"],
                "provider": {"anthropic": {"options": {"timeout": 120000}}},
            },
        )
        self.assertIsNone(updated_marker)
        self.assertIn("CLIProxyAPI provider disabled", output)

    def test_disabled_provider_does_not_change_other_configuration(self):
        original = {
            "plugin": ["opencode-claude-auth@2.2.0"],
            "provider": {"anthropic": {"options": {"timeout": 120000}}},
        }
        updated, marker, output = self.run_provider(original, enabled="false")

        self.assertEqual(updated, original)
        self.assertIsNone(marker)
        self.assertEqual(output, "")


if __name__ == "__main__":
    unittest.main()
