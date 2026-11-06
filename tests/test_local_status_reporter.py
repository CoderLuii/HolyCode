import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
REPORTER = ROOT / "scripts" / "report_local_status.py"
SOURCE_STAGES = (
    "python-tests", "workflow-pins", "chromium-seccomp", "renovate-json",
    "npm-policy-json", "workflow-yaml", "compose-default", "compose-full",
    "external-cliproxy-absent", "renovate-extraction",
)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


class LocalStatusReporterTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(REPORTER.exists(), "the local evidence reporter is missing")
        spec = importlib.util.spec_from_file_location("local_reporter", REPORTER)
        self.reporter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.reporter)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.evidence_root = self.root / "evidence"
        self.evidence_root.mkdir()
        self.state_dir = self.root / "state"
        self.env = {key: os.environ[key] for key in ("PATH", "SystemRoot", "TEMP", "TMP") if key in os.environ}
        self.env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
        self.git("init", "-q")
        (self.repo / "input.txt").write_bytes(b"qualified source\n")
        (self.repo / "second.txt").write_bytes(b"second retained file\n")
        (self.repo / "Dockerfile").write_text(
            "FROM scratch\nCOPY --chmod=0755 input.txt /input.txt\n"
            "COPY second.txt /usr/share/second.txt\nCOPY input.txt /tmp/build-only.txt\n",
            encoding="utf-8")
        self.git("add", "input.txt", "second.txt", "Dockerfile")
        self.git("-c", "user.name=Local Test", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", "-c", "core.hooksPath=" + os.devnull,
                 "commit", "-qm", "fixture")
        self.sha = self.git("rev-parse", "HEAD").strip()
        files = []
        for name in ("Dockerfile", "input.txt", "second.txt"):
            raw = (self.repo / name).read_bytes()
            files.append({"path": name, "mode": "100644",
                          "blob_sha1": self.git("rev-parse", "HEAD:" + name).strip(),
                          "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        source = {
            "schema": 1, "repository": "CoderLuii/HolyCode", "sha": self.sha,
            "tree": self.git("rev-parse", "HEAD^{tree}").strip(),
            "files": files,
        }
        self.source = self.write("source.json", encoded(source))
        self.identity = {"repository": "CoderLuii/HolyCode", "sha": self.sha,
                         "run_id": "attempt-1", "context": "local/source-validation"}
        self.plan = dict(self.identity, schema=1, repo_dir=str(self.repo),
                         evidence_root=str(self.evidence_root), source_manifest=self.source,
                         source_sha256=self.source["sha256"],
                         tools=[self.write("controller.py", b"# trusted controller fixture\n")], stages=[
                             {"id": stage, "argv": ["python", "validate.py", stage],
                              "cwd": str(self.repo), "required_artifacts": []}
                             for stage in SOURCE_STAGES])
        self.plan_path = self.evidence_root / "plan.json"
        self.plan_path.write_bytes(encoded(self.plan))
        self.transport = mock.Mock(side_effect=self.remote)

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.repo), *args], env=self.env,
                                capture_output=True, text=True, check=True)
        return result.stdout

    def write(self, name, raw):
        path = self.evidence_root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return {"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

    def remote(self, method, path, payload=None):
        if method == "GET":
            return {"sha": self.sha}, {"X-OAuth-Scopes": "repo"}
        return {"id": 1, "state": payload["state"], "context": payload["context"]}, {}

    def run_reporter(self, action, **kwargs):
        return self.reporter.run(action, self.state_dir, **self.identity,
                                 transport=self.transport, **kwargs)

    def begin(self, published=False):
        return self.run_reporter("begin", plan_file=self.plan_path, published=published)

    def evidence(self, exit_code=0, outcome="completed"):
        started = datetime.now(timezone.utc)
        stamp = started.isoformat().replace("+00:00", "Z")
        end = (started + timedelta(microseconds=1)).isoformat().replace("+00:00", "Z")
        plan_sha = hashlib.sha256(self.plan_path.read_bytes()).hexdigest()
        receipts = []
        for index, stage in enumerate(self.plan["stages"]):
            receipt = dict(self.identity, schema=1, source_sha256=self.source["sha256"],
                           plan_sha256=plan_sha, stage=stage["id"], argv=stage["argv"],
                           cwd=stage["cwd"], started_at=stamp, finished_at=end,
                           exit_code=exit_code if index == 0 else 0,
                           stdout=self.write(stage["id"] + ".stdout", b"checked\n"),
                           stderr=self.write(stage["id"] + ".stderr", b""), artifacts=[])
            receipts.append(self.write(stage["id"] + ".json", encoded(receipt)))
        evidence = dict(self.identity, schema=1, source_sha256=self.source["sha256"],
                        plan_sha256=plan_sha, started_at=stamp, finished_at=end,
                        outcome=outcome, source_before=self.source,
                        source_after=self.source, receipts=receipts)
        path = self.evidence_root / "evidence.json"
        path.write_bytes(encoded(evidence))
        return path

    def mutate_evidence(self, path, mutate):
        evidence = json.loads(path.read_bytes())
        mutate(evidence)
        path.write_bytes(encoded(evidence))

    def mutate_receipt(self, path, mutate):
        evidence = json.loads(path.read_bytes())
        descriptor = evidence["receipts"][0]
        receipt = json.loads((self.evidence_root / descriptor["path"]).read_bytes())
        mutate(receipt)
        evidence["receipts"][0] = self.write(descriptor["path"], encoded(receipt))
        path.write_bytes(encoded(evidence))

    def test_unpublished_run_stays_local_until_sync(self):
        self.assertEqual(self.begin()["state"], "pending")
        result = self.run_reporter("finish", evidence_file=self.evidence())
        self.assertEqual(result["state"], "success")
        self.transport.assert_not_called()
        result = self.run_reporter("sync")
        self.assertTrue(result["synced"])
        posts = [call.args for call in self.transport.call_args_list if call.args[0] == "POST"]
        self.assertEqual([call[2]["state"] for call in posts], ["pending", "success"])
        self.assertTrue(all(self.sha in call[1] for call in posts))
        self.assertTrue(all("target_url" not in call[2] for call in posts))

    def test_published_begin_posts_pending_before_commands(self):
        result = self.begin(published=True)
        self.assertEqual(result["state"], "pending")
        self.assertEqual(self.transport.call_args.args[2]["state"], "pending")

    def test_nonzero_command_is_failure_even_with_completed_claim(self):
        self.begin()
        result = self.run_reporter("finish", evidence_file=self.evidence(exit_code=9))
        self.assertEqual(result["state"], "failure")

    def test_interrupted_unknown_and_missing_execution_never_green(self):
        self.begin()
        path = self.evidence(outcome="interrupted")
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "error")

    def test_pass_flag_without_command_receipts_is_error(self):
        self.begin()
        path = self.evidence()
        self.mutate_evidence(path, lambda evidence: evidence.update(receipts=[], passed=True))
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "error")

    def test_changed_stream_digest_is_error(self):
        self.begin()
        path = self.evidence()
        (self.evidence_root / "python-tests.stdout").write_bytes(b"substituted")
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "error")

    def test_changed_registered_command_is_error(self):
        self.begin()
        path = self.evidence()
        self.mutate_receipt(path, lambda receipt: receipt.update(argv=["true"]))
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "error")

    def test_wrong_identity_is_error(self):
        self.begin()
        path = self.evidence()
        self.mutate_receipt(path, lambda receipt: receipt.update(sha="a" * 40))
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "error")

    def test_missing_mandatory_stage_is_rejected_before_begin(self):
        self.plan["stages"].pop()
        self.plan_path.write_bytes(encoded(self.plan))
        with self.assertRaises(ValueError):
            self.begin()

    def test_plan_digest_cannot_be_replaced_after_begin(self):
        self.begin()
        self.plan["stages"][0]["argv"] = ["true"]
        self.plan_path.write_bytes(encoded(self.plan))
        self.assertEqual(self.run_reporter("finish", evidence_file=self.evidence())["state"], "error")

    def test_tracked_source_mutation_is_error(self):
        self.begin()
        path = self.evidence()
        (self.repo / "input.txt").write_bytes(b"changed\n")
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "error")

    def test_source_rechecked_before_remote_success(self):
        self.begin()
        self.run_reporter("finish", evidence_file=self.evidence())
        (self.repo / "input.txt").write_bytes(b"changed\n")
        result = self.run_reporter("sync")
        self.assertEqual(result["state"], "error")
        self.assertEqual(self.transport.call_args.args[2]["state"], "error")

    def test_stale_run_cannot_finish_or_sync(self):
        self.begin()
        old_evidence = self.evidence()
        old_identity = self.identity.copy()
        self.identity["run_id"] = "attempt-2"
        self.plan["run_id"] = self.identity["run_id"]
        self.plan_path.write_bytes(encoded(self.plan))
        self.assertEqual(self.begin()["attempt"], 2)
        self.identity = old_identity
        for action in ("finish", "sync"):
            with self.subTest(action=action), self.assertRaises(ValueError):
                self.run_reporter(action, evidence_file=old_evidence)
        self.transport.assert_not_called()

    def test_run_id_cannot_be_reused(self):
        self.begin()
        with self.assertRaises(ValueError):
            self.begin()

    def test_no_success_without_finish(self):
        self.begin()
        result = self.run_reporter("sync")
        self.assertEqual(result["state"], "pending")
        self.assertEqual(self.transport.call_args.args[2]["state"], "pending")

    def test_api_denial_does_not_record_synced_success(self):
        self.begin()
        self.run_reporter("finish", evidence_file=self.evidence())
        self.transport.side_effect = ValueError("GitHub API denied access")
        with self.assertRaises(ValueError):
            self.run_reporter("sync")
        self.transport.side_effect = self.remote
        self.assertTrue(self.run_reporter("sync")["synced"])

    def test_commit_identity_mismatch_never_posts(self):
        self.begin()
        self.transport.side_effect = lambda *args: ({"sha": "b" * 40}, {})
        with self.assertRaises(ValueError):
            self.run_reporter("sync")
        self.assertEqual(len(self.transport.call_args_list), 1)

    def test_known_insufficient_token_scopes_never_posts(self):
        self.begin()
        self.transport.side_effect = lambda *args: ({"sha": self.sha}, {"X-OAuth-Scopes": "read:user"})
        with self.assertRaises(ValueError):
            self.run_reporter("sync")
        self.assertEqual(len(self.transport.call_args_list), 1)

    def test_success_cannot_be_repaired_under_same_run(self):
        self.begin()
        path = self.evidence(exit_code=2)
        self.run_reporter("finish", evidence_file=path)
        with self.assertRaises(ValueError):
            self.run_reporter("finish", evidence_file=self.evidence())

    def test_duplicate_json_keys_are_rejected(self):
        self.begin()
        path = self.evidence_root / "invalid.json"
        path.write_text('{"outcome":"interrupted","outcome":"completed"}', encoding="utf-8")
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "error")

    def test_lock_blocks_second_owner_and_recovers_after_release(self):
        self.state_dir.mkdir()
        with self.reporter.state_lock(self.state_dir):
            with self.assertRaises(ValueError):
                with self.reporter.state_lock(self.state_dir):
                    self.fail("second reporter acquired active lock")
        with self.reporter.state_lock(self.state_dir):
            pass

    def test_failed_published_pending_prevents_execution_completion(self):
        self.transport.side_effect = ValueError("permission denied")
        with self.assertRaises(ValueError):
            self.begin(published=True)
        with self.assertRaises(ValueError):
            self.run_reporter("finish", evidence_file=self.evidence())

    def test_unknown_command_exit_is_error(self):
        self.begin()
        path = self.evidence()
        self.mutate_receipt(path, lambda receipt: receipt.update(exit_code=None))
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "error")

    def test_missing_required_artifact_is_error(self):
        self.plan["stages"][0]["required_artifacts"] = ["report"]
        self.plan_path.write_bytes(encoded(self.plan))
        self.begin()
        self.assertEqual(self.run_reporter("finish", evidence_file=self.evidence())["state"], "error")

    def test_artifact_bytes_are_rechecked_before_sync(self):
        self.plan["stages"][0]["required_artifacts"] = ["report"]
        self.plan_path.write_bytes(encoded(self.plan))
        self.begin()
        path = self.evidence()
        artifact = dict(self.write("report.txt", b"checked contents\n"), role="report")
        self.mutate_receipt(path, lambda receipt: receipt.update(artifacts=[artifact]))
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "success")
        (self.evidence_root / "report.txt").write_bytes(b"tampered contents\n")
        self.assertEqual(self.run_reporter("sync")["state"], "error")
        self.assertNotIn("success", [call.args[2]["state"] for call in self.transport.call_args_list if call.args[0] == "POST"])

    def test_path_traversal_is_error(self):
        self.begin()
        path = self.evidence()
        self.mutate_receipt(path, lambda receipt: receipt["stdout"].update(path="../outside.txt"))
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "error")

    def test_duplicate_stage_receipt_is_error(self):
        self.begin()
        path = self.evidence()
        self.mutate_evidence(path, lambda evidence: evidence["receipts"].append(evidence["receipts"][0]))
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "error")

    def test_previous_attempt_timestamps_are_error(self):
        self.begin()
        path = self.evidence()
        self.mutate_evidence(path, lambda evidence: evidence.update(started_at="2020-01-01T00:00:00Z"))
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "error")

    def test_unpublished_flag_cannot_skip_remote_pending_after_published_attempt(self):
        self.begin(published=True)
        self.run_reporter("finish", evidence_file=self.evidence())
        self.run_reporter("sync")
        self.transport.reset_mock()
        self.identity["run_id"] = "attempt-2"
        self.plan["run_id"] = self.identity["run_id"]
        self.plan_path.write_bytes(encoded(self.plan))
        self.begin()
        self.assertEqual(self.transport.call_args.args[2]["state"], "pending")

    def test_terminating_lock_owner_releases_os_lock(self):
        self.state_dir.mkdir()
        code = (
            "import importlib.util,os,pathlib; "
            f"s=importlib.util.spec_from_file_location('reporter',{str(REPORTER)!r}); "
            "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
            f"lock=m.state_lock(pathlib.Path({str(self.state_dir)!r})); "
            "lock.__enter__(); os._exit(23)"
        )
        child = subprocess.run([sys.executable, "-B", "-c", code], env=self.env, capture_output=True, timeout=10)
        self.assertEqual(child.returncode, 23)
        with self.reporter.state_lock(self.state_dir):
            pass

    def test_source_descriptor_cannot_lie_about_tree(self):
        source = json.loads((self.evidence_root / "source.json").read_bytes())
        source["tree"] = "c" * 40
        self.source = self.write("source.json", encoded(source))
        self.plan.update(source_manifest=self.source, source_sha256=self.source["sha256"])
        self.plan_path.write_bytes(encoded(self.plan))
        with self.assertRaises(ValueError):
            self.begin()

    def test_symlink_artifact_cannot_escape_evidence_root(self):
        outside = self.root / "outside.txt"
        outside.write_bytes(b"outside")
        try:
            (self.evidence_root / "linked.txt").symlink_to(outside)
        except OSError:
            self.skipTest("OS does not allow creating symlinks")
        record = {"path": "linked.txt", "bytes": 7, "sha256": hashlib.sha256(b"outside").hexdigest()}
        with self.assertRaises(ValueError):
            self.reporter.read_record(self.evidence_root, record)

    def test_fine_grained_token_without_scope_metadata_uses_real_pending(self):
        self.transport.side_effect = lambda method, path, payload=None: (
            ({"sha": self.sha}, {"X-OAuth-Scopes": ""}) if method == "GET"
            else ({"state": payload["state"], "context": payload["context"]}, {})
        )
        self.assertTrue(self.begin(published=True)["synced"])

    def test_api_transport_keeps_token_out_of_arguments_and_refuses_redirect(self):
        response = mock.Mock(status=302)
        connection = mock.Mock()
        connection.getresponse.return_value = response
        fake_auth = subprocess.CompletedProcess([], 0, b"test-only-token-value\n", b"")
        with mock.patch.object(self.reporter.shutil, "which", return_value="gh"), \
                mock.patch.object(self.reporter.subprocess, "run", return_value=fake_auth) as auth, \
                mock.patch.object(self.reporter.http.client, "HTTPSConnection", return_value=connection):
            with self.assertRaisesRegex(ValueError, "HTTP 302"):
                self.reporter.github_request("GET", "/repos/CoderLuii/HolyCode/commits/" + self.sha)
        self.assertNotIn("test-only-token-value", str(auth.call_args))
        connection.request.assert_called_once()
        connection.close.assert_called_once()

    def test_native_plan_cannot_omit_required_scanner_artifact(self):
        self.identity["context"] = "local/native-amd64"
        self.plan.update(context=self.identity["context"], stages=[
            {"id": stage, "argv": ["bash", stage], "cwd": str(self.repo), "required_artifacts": []}
            for stage in sorted(self.reporter.NATIVE_STAGES)
        ])
        self.plan_path.write_bytes(encoded(self.plan))
        with self.assertRaises(ValueError):
            self.begin()

    def native_artifacts(self):
        digest = lambda letter: "sha256:" + letter * 64
        self.plan["context"] = "local/native-amd64"
        self.plan["native_firstparty_files"] = [
            {"source": "input.txt", "destination": "/input.txt"},
            {"source": "second.txt", "destination": "/usr/share/second.txt"}]
        identity = {"source_sha": self.sha, "platform": "linux/amd64",
                    "candidate_digest": digest("a"), "native_index_digest": digest("b"),
                    "engine_image_id": digest("b"), "engine_platform_id": digest("c"),
                    "manifest_digest": digest("c"), "config_digest": digest("d"),
                    "diff_ids": [digest("e")]}
        source_files = {file["path"]: file for file in
                        json.loads((self.evidence_root / "source.json").read_bytes())["files"]}
        firstparty = dict(identity, files=[
            dict(mapping, size=source_files[mapping["source"]]["bytes"],
                 actual_size=source_files[mapping["source"]]["bytes"],
                 sha256=source_files[mapping["source"]]["sha256"],
                 actual_sha256=source_files[mapping["source"]]["sha256"], matches=True)
            for mapping in self.plan["native_firstparty_files"]])
        provenance = {"source_sha": self.sha, "candidate_digest": digest("a"), "platforms": [
            {"platform": "linux/amd64", "manifest_digest": digest("c"),
             "config_digest": digest("d"), "rootfs_diff_ids": [digest("e")],
             "attestation_digest": digest("f"), "package_count": 10,
             "provenance_origin": "local BuildKit"}]}
        return {"native-identity": identity, "firstparty": firstparty, "provenance": provenance}

    def test_native_artifacts_agree_on_source_and_image_graph(self):
        self.assertTrue(hasattr(self.reporter, "validate_native_artifacts"), "native identity validation missing")
        self.reporter.validate_native_artifacts(self.plan, self.native_artifacts())

    def test_native_candidate_digest_mismatch_is_rejected(self):
        self.assertTrue(hasattr(self.reporter, "validate_native_artifacts"), "native identity validation missing")
        artifacts = self.native_artifacts()
        artifacts["provenance"]["candidate_digest"] = "sha256:" + "f" * 64
        with self.assertRaises(ValueError):
            self.reporter.validate_native_artifacts(self.plan, artifacts)

    def test_native_firstparty_pass_flag_cannot_hide_different_bytes(self):
        self.assertTrue(hasattr(self.reporter, "validate_native_artifacts"), "native identity validation missing")
        artifacts = self.native_artifacts()
        artifacts["firstparty"]["files"][0]["actual_sha256"] = "e" * 64
        with self.assertRaises(ValueError):
            self.reporter.validate_native_artifacts(self.plan, artifacts)

    def test_native_firstparty_cannot_omit_registered_mapping(self):
        self.assertTrue(hasattr(self.reporter, "validate_native_artifacts"), "native identity validation missing")
        artifacts = self.native_artifacts()
        artifacts["firstparty"]["files"] = []
        with self.assertRaises(ValueError):
            self.reporter.validate_native_artifacts(self.plan, artifacts)

    def test_registered_controller_change_is_error(self):
        self.begin()
        path = self.evidence()
        (self.evidence_root / "controller.py").write_bytes(b"changed controller\n")
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "error")

    def native_evidence(self):
        artifacts = self.native_artifacts()
        self.identity["context"] = self.plan["context"]
        self.plan["stages"] = [
            {"id": stage, "argv": ["python", "stage.py", stage], "cwd": str(self.repo),
             "inner_argv": ["docker", "inspect", "fixture"], "inner_cwd": "/source",
             "inner_wrapper_sha256": self.plan["tools"][0]["sha256"],
             "required_artifacts": sorted(self.reporter.NATIVE_ARTIFACTS.get(stage, set()))}
            for stage in sorted(self.reporter.NATIVE_STAGES)
        ]
        self.plan_path.write_bytes(encoded(self.plan))
        self.begin()
        path = self.evidence()
        evidence = json.loads(path.read_bytes())
        for index, stage in enumerate(self.plan["stages"]):
            descriptor = evidence["receipts"][index]
            receipt = json.loads((self.evidence_root / descriptor["path"]).read_bytes())
            spec = {key: receipt[key] for key in ("stage", "sha", "run_id", "context", "source_sha256", "plan_sha256")}
            receipt.update(shared_job_id="1234567890abcdef", shared_owner="hf-holycode-1234567890abcdef")
            spec.update(argv=stage["inner_argv"], cwd=stage["inner_cwd"],
                        shared_job_id=receipt["shared_job_id"], shared_owner=receipt["shared_owner"],
                        wrapper_sha256=stage["inner_wrapper_sha256"])
            spec_record = self.write(stage["id"] + ".command-spec.json", encoded(spec))
            inner = dict(spec, spec_sha256=spec_record["sha256"], started_at=receipt["started_at"],
                         finished_at=receipt["finished_at"], exit_code=receipt["exit_code"],
                         stdout=receipt["stdout"], stderr=receipt["stderr"])
            receipt["artifacts"] = [
                dict(self.write(role + ".artifact", encoded(artifacts.get(role, {"raw_report": "fixture"}))), role=role)
                for role in stage["required_artifacts"] if role not in {"inner-command", "inner-spec"}
            ]
            receipt["artifacts"].extend([
                dict(spec_record, role="inner-spec"),
                dict(self.write(stage["id"] + ".inner-command.json", encoded(inner)), role="inner-command"),
            ])
            evidence["receipts"][index] = self.write(descriptor["path"], encoded(receipt))
        path.write_bytes(encoded(evidence))
        return path

    def test_full_native_evidence_requires_every_stage_and_artifact(self):
        self.assertEqual(self.run_reporter("finish", evidence_file=self.native_evidence())["state"], "success")

    def test_full_native_evidence_rejects_resealed_wrong_candidate(self):
        path = self.native_evidence()
        evidence = json.loads(path.read_bytes())
        for index, descriptor in enumerate(evidence["receipts"]):
            receipt = json.loads((self.evidence_root / descriptor["path"]).read_bytes())
            if receipt["stage"] == "provenance":
                artifact = receipt["artifacts"][0]
                provenance = json.loads((self.evidence_root / artifact["path"]).read_bytes())
                provenance["candidate_digest"] = "sha256:" + "1" * 64
                receipt["artifacts"][0] = dict(self.write(artifact["path"], encoded(provenance)), role="provenance")
                evidence["receipts"][index] = self.write(descriptor["path"], encoded(receipt))
        path.write_bytes(encoded(evidence))
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "error")

    def release_artifacts(self):
        self.plan["context"] = "local/release-integrity"
        self.plan["release"] = {"id": 321, "tag": "v1.3.0", "sha": self.sha,
                                "candidate_digest": "sha256:" + "a" * 64}
        documents = {stage: {"release_id": 321, "release_tag": "v1.3.0", "source_sha": self.sha,
                            "candidate_digest": "sha256:" + "a" * 64,
                            "reports": [self.write(stage + ".raw.json", b'{"readback":"fixture"}\n')]}
                     for stage in self.reporter.RELEASE_STAGES}
        documents["release-identity"].update(draft=False, tag_sha=self.sha, published_at="2026-01-01T00:00:00Z")
        return documents

    def test_release_artifacts_bind_published_release_and_exact_commit(self):
        self.assertTrue(hasattr(self.reporter, "validate_release_artifacts"), "release identity validation missing")
        self.reporter.validate_release_artifacts(self.plan, self.release_artifacts(), "2026-01-02T00:00:00Z")

    def test_release_draft_cannot_pass_integrity(self):
        self.assertTrue(hasattr(self.reporter, "validate_release_artifacts"), "release identity validation missing")
        documents = self.release_artifacts()
        documents["release-identity"]["draft"] = True
        with self.assertRaises(ValueError):
            self.reporter.validate_release_artifacts(self.plan, documents, "2026-01-02T00:00:00Z")

    def test_release_other_tag_or_candidate_cannot_pass_integrity(self):
        self.assertTrue(hasattr(self.reporter, "validate_release_artifacts"), "release identity validation missing")
        documents = self.release_artifacts()
        documents["release-assets"]["release_tag"] = "v1.2.9"
        with self.assertRaises(ValueError):
            self.reporter.validate_release_artifacts(self.plan, documents, "2026-01-02T00:00:00Z")

    def test_release_checks_before_publication_cannot_pass(self):
        self.assertTrue(hasattr(self.reporter, "validate_release_artifacts"), "release identity validation missing")
        documents = self.release_artifacts()
        with self.assertRaises(ValueError):
            self.reporter.validate_release_artifacts(self.plan, documents, "2025-12-31T00:00:00Z")

    def test_junction_evidence_root_is_rejected(self):
        with mock.patch.object(Path, "is_junction", lambda path: path == self.evidence_root, create=True):
            with self.assertRaises(ValueError):
                self.reporter.read_record(self.evidence_root, self.source)

    def inner_command_fixture(self):
        self.plan["stages"][0].update(inner_argv=["docker", "build", "."], inner_cwd="/source",
                                     inner_wrapper_sha256=self.plan["tools"][0]["sha256"],
                                     required_artifacts=["inner-command", "inner-spec"])
        self.plan_path.write_bytes(encoded(self.plan))
        self.begin()
        path = self.evidence()
        evidence = json.loads(path.read_bytes())
        outer = json.loads((self.evidence_root / evidence["receipts"][0]["path"]).read_bytes())
        spec = {key: outer[key] for key in ("stage", "sha", "run_id", "context", "source_sha256", "plan_sha256")}
        outer.update(shared_job_id="1234567890abcdef", shared_owner="hf-holycode-1234567890abcdef")
        spec.update(argv=["docker", "build", "."], cwd="/source", shared_job_id=outer["shared_job_id"],
                    shared_owner=outer["shared_owner"], wrapper_sha256=self.plan["tools"][0]["sha256"])
        spec_record = self.write("command-spec.json", encoded(spec))
        inner = dict(spec, spec_sha256=spec_record["sha256"], started_at=outer["started_at"],
                     finished_at=outer["finished_at"], exit_code=outer["exit_code"],
                     stdout=outer["stdout"], stderr=outer["stderr"])
        return outer, inner, spec_record

    def test_inner_command_matches_sealed_spec_and_outer_streams(self):
        self.assertTrue(hasattr(self.reporter, "validate_inner_command"), "inner command validation missing")
        outer, inner, spec_record = self.inner_command_fixture()
        self.reporter.validate_inner_command(self.plan, outer, inner, spec_record)

    def test_inner_command_argv_change_cannot_hide_behind_outer_wrapper(self):
        self.assertTrue(hasattr(self.reporter, "validate_inner_command"), "inner command validation missing")
        outer, inner, spec_record = self.inner_command_fixture()
        inner["argv"] = ["true"]
        with self.assertRaises(ValueError):
            self.reporter.validate_inner_command(self.plan, outer, inner, spec_record)

    def test_inner_command_stream_change_cannot_hide_behind_outer_wrapper(self):
        self.assertTrue(hasattr(self.reporter, "validate_inner_command"), "inner command validation missing")
        outer, inner, spec_record = self.inner_command_fixture()
        inner["stdout"] = dict(inner["stdout"], sha256="f" * 64)
        with self.assertRaises(ValueError):
            self.reporter.validate_inner_command(self.plan, outer, inner, spec_record)

    def next_attempt(self, number):
        self.identity["run_id"] = "attempt-" + str(number)
        self.plan["run_id"] = self.identity["run_id"]
        self.plan_path.write_bytes(encoded(self.plan))

    def stored_state(self):
        return json.loads(next(self.state_dir.glob("*.json")).read_bytes())

    def test_denied_pending_keeps_publication_known_across_attempts(self):
        self.begin(published=True)
        self.run_reporter("finish", evidence_file=self.evidence())
        self.run_reporter("sync")
        self.next_attempt(2)

        def denied(method, path, payload=None):
            if method == "POST":
                raise ValueError("pending denied")
            return self.remote(method, path, payload)

        self.transport.side_effect = denied
        with self.assertRaises(ValueError):
            self.begin()
        self.assertEqual(self.stored_state()["state"], "error")
        self.next_attempt(3)
        self.transport.reset_mock()
        self.transport.side_effect = self.remote
        self.assertTrue(self.begin()["synced"])
        self.assertEqual(self.transport.call_args.args[2]["state"], "pending")

    def test_remote_knowledge_is_saved_before_first_request(self):
        def inspect_before_request(method, path, payload=None):
            self.assertTrue(self.stored_state().get("remote_known"))
            return self.remote(method, path, payload)

        self.transport.side_effect = inspect_before_request
        self.begin(published=True)

    def test_crashed_sync_requires_remote_pending_on_next_attempt(self):
        self.begin()
        self.run_reporter("finish", evidence_file=self.evidence())
        self.crash_remote_request("sync")
        self.next_attempt(2)
        self.assertTrue(self.begin()["synced"])
        self.assertEqual(self.transport.call_args.args[2]["state"], "pending")

    def crash_remote_request(self, action):
        code = (
            "import importlib.util,os; "
            f"s=importlib.util.spec_from_file_location('reporter',{str(REPORTER)!r}); "
            "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
            f"m.run({action!r},{str(self.state_dir)!r},**{self.identity!r},"
            f"plan_file={str(self.plan_path)!r},published=True,"
            "transport=lambda *args: os._exit(23))"
        )
        child = subprocess.run([sys.executable, "-B", "-c", code], env=self.env,
                               capture_output=True, timeout=10)
        self.assertEqual(child.returncode, 23, child.stderr.decode())

    def test_crashed_published_begin_cannot_finish_without_pending_ack(self):
        self.crash_remote_request("begin")
        self.assertEqual(self.run_reporter("finish", evidence_file=self.evidence())["state"], "error")

    def test_crashed_published_begin_keeps_remote_requirement_on_retry(self):
        self.crash_remote_request("begin")
        self.next_attempt(2)
        self.assertTrue(self.begin()["synced"])
        self.assertEqual(self.transport.call_args.args[2]["state"], "pending")

    def mutate_inner_artifacts(self, path, mutate, stage_id="native-build"):
        evidence = json.loads(path.read_bytes())
        for index, record in enumerate(evidence["receipts"]):
            outer = json.loads((self.evidence_root / record["path"]).read_bytes())
            if outer["stage"] != stage_id:
                continue
            records = {item["role"]: item for item in outer["artifacts"]}
            spec = json.loads((self.evidence_root / records["inner-spec"]["path"]).read_bytes())
            inner = json.loads((self.evidence_root / records["inner-command"]["path"]).read_bytes())
            mutate(outer, spec, inner)
            records["inner-spec"] = dict(self.write(records["inner-spec"]["path"], encoded(spec)), role="inner-spec")
            inner["spec_sha256"] = records["inner-spec"]["sha256"]
            records["inner-command"] = dict(self.write(records["inner-command"]["path"], encoded(inner)), role="inner-command")
            outer["artifacts"] = list(records.values())
            evidence["receipts"][index] = self.write(record["path"], encoded(outer))
            path.write_bytes(encoded(evidence))
            return
        self.fail("fixture stage missing")

    def test_native_resealed_inner_argv_cannot_replace_registered_command(self):
        path = self.native_evidence()
        self.mutate_inner_artifacts(path, lambda outer, spec, inner:
                                    (spec.update(argv=["true"]), inner.update(argv=["true"])))
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "error")

    def test_native_resealed_inner_cwd_cannot_replace_registered_directory(self):
        path = self.native_evidence()
        self.mutate_inner_artifacts(path, lambda outer, spec, inner:
                                    (spec.update(cwd="/different"), inner.update(cwd="/different")))
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "error")

    def source_inner_evidence(self):
        outer, inner, spec_record = self.inner_command_fixture()
        outer["artifacts"] = [dict(spec_record, role="inner-spec"),
                              dict(self.write("source-inner.json", encoded(inner)), role="inner-command")]
        path = self.evidence_root / "evidence.json"
        self.mutate_receipt(path, lambda receipt: receipt.update(outer))
        return path

    def test_source_registered_inner_command_has_full_finish_validation(self):
        self.assertEqual(self.run_reporter("finish", evidence_file=self.source_inner_evidence())["state"], "success")

    def test_source_resealed_inner_command_cannot_bypass_registered_plan(self):
        path = self.source_inner_evidence()
        self.mutate_inner_artifacts(path, lambda outer, spec, inner:
                                    (spec.update(argv=["true"]), inner.update(argv=["true"])),
                                    stage_id="python-tests")
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "error")

    def test_inner_wrapper_must_equal_registered_stage_not_just_any_tool(self):
        outer, inner, spec_record = self.inner_command_fixture()
        other = self.write("other-tool.py", b"other registered controller tool\n")
        self.plan["tools"].append(other)
        spec = json.loads((self.evidence_root / spec_record["path"]).read_bytes())
        spec["wrapper_sha256"] = other["sha256"]
        spec_record = self.write(spec_record["path"], encoded(spec))
        inner.update(wrapper_sha256=other["sha256"], spec_sha256=spec_record["sha256"])
        with self.assertRaises(ValueError):
            self.reporter.validate_inner_command(self.plan, outer, inner, spec_record)

    def test_native_plan_requires_exact_inner_command_fields(self):
        self.native_evidence()
        for field in ("inner_argv", "inner_cwd", "inner_wrapper_sha256"):
            original = self.plan["stages"][0].pop(field)
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.reporter.validate_plan(self.plan, self.identity)
            self.plan["stages"][0][field] = original

    def test_native_job_ownership_cannot_be_null_in_all_records(self):
        path = self.native_evidence()
        self.mutate_inner_artifacts(path, lambda outer, spec, inner:
                                    [record.update(shared_job_id=None, shared_owner=None)
                                     for record in (outer, spec, inner)])
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "error")

    def test_native_job_ownership_must_match_admission_identity(self):
        path = self.native_evidence()
        self.mutate_inner_artifacts(path, lambda outer, spec, inner:
                                    outer.update(shared_job_id="abcdef1234567890",
                                                 shared_owner="hf-holycode-abcdef1234567890"))
        self.assertEqual(self.run_reporter("finish", evidence_file=path)["state"], "error")

    def test_native_job_ownership_format_and_owner_are_required(self):
        outer, inner, spec_record = self.inner_command_fixture()
        for job, owner in (("job-123", "hf-holycode-job-123"),
                           ("1234567890abcdef", "other-1234567890abcdef"), ("", "")):
            spec = json.loads((self.evidence_root / spec_record["path"]).read_bytes())
            for record in (outer, spec, inner):
                record.update(shared_job_id=job, shared_owner=owner)
            spec_record = self.write(spec_record["path"], encoded(spec))
            inner["spec_sha256"] = spec_record["sha256"]
            with self.subTest(job=job, owner=owner), self.assertRaises(ValueError):
                self.reporter.validate_inner_command(self.plan, outer, inner, spec_record)

    def test_git_replacement_bytes_cannot_pass_under_original_commit(self):
        source = json.loads((self.evidence_root / "source.json").read_bytes())
        entry = next(item for item in source["files"] if item["path"] == "input.txt")
        original_blob = entry["blob_sha1"]
        changed = b"different bytes under a replaced Git blob\n"
        (self.repo / "replacement.txt").write_bytes(changed)
        replacement = self.git("hash-object", "-w", "replacement.txt").strip()
        self.git("replace", original_blob, replacement)
        (self.repo / "input.txt").write_bytes(changed)
        entry.update(bytes=len(changed), sha256=hashlib.sha256(changed).hexdigest())
        self.source = self.write("source.json", encoded(source))
        self.plan.update(source_manifest=self.source, source_sha256=self.source["sha256"])
        self.plan_path.write_bytes(encoded(self.plan))
        self.assertEqual(self.git("cat-file", "blob", original_blob), changed.decode())
        self.assertEqual(self.git("--no-replace-objects", "cat-file", "blob", original_blob), "qualified source\n")
        with self.assertRaises(ValueError):
            self.begin()

    def test_git_reads_disable_replacement_objects_in_command_and_environment(self):
        result = subprocess.CompletedProcess([], 0, b"fixture", b"")
        with mock.patch.object(self.reporter.subprocess, "run", return_value=result) as process:
            self.reporter.git(self.repo, "cat-file", "blob", "a" * 40)
        self.assertIn("--no-replace-objects", process.call_args.args[0])
        self.assertEqual(process.call_args.kwargs["env"].get("GIT_NO_REPLACE_OBJECTS"), "1")

    def test_source_independently_checks_raw_blob_sha1(self):
        original_git = self.reporter.git
        original_blob = self.git("rev-parse", "HEAD:input.txt").strip().encode()
        source = json.loads((self.evidence_root / "source.json").read_bytes())
        next(item for item in source["files"] if item["path"] == "input.txt")["blob_sha1"] = "a" * 40
        self.source = self.write("source.json", encoded(source))
        self.plan.update(source_manifest=self.source, source_sha256=self.source["sha256"])

        def lied_blob(repo, *args):
            if args == ("cat-file", "blob", "a" * 40):
                return b"qualified source\n"
            raw = original_git(repo, *args)
            if args[0] in {"ls-tree", "ls-files"}:
                return raw.replace(original_blob, b"a" * 40)
            return raw

        with mock.patch.object(self.reporter, "git", side_effect=lied_blob):
            with self.assertRaisesRegex(ValueError, "blob identity"):
                self.reporter.verify_source(self.plan)

    def test_native_mapping_registration_must_cover_committed_dockerfile(self):
        self.native_evidence()
        self.plan["native_firstparty_files"] = self.plan["native_firstparty_files"][:1]
        with self.assertRaises(ValueError):
            self.reporter.validate_plan(self.plan, self.identity)

    def test_native_mapping_artifacts_cannot_hide_unregistered_retained_copy(self):
        artifacts = self.native_artifacts()
        self.plan["native_firstparty_files"] = self.plan["native_firstparty_files"][:1]
        artifacts["firstparty"]["files"] = artifacts["firstparty"]["files"][:1]
        with self.assertRaises(ValueError):
            self.reporter.validate_native_artifacts(self.plan, artifacts)

    def test_native_invalid_inner_timestamp_is_journaled_and_cli_is_private(self):
        path = self.native_evidence()
        self.mutate_inner_artifacts(path, lambda outer, spec, inner: inner.update(started_at=None))
        result = subprocess.run([
            sys.executable, "-B", str(REPORTER), "finish", "--state-dir", str(self.state_dir),
            "--repo", self.identity["repository"], "--sha", self.sha, "--run-id", self.identity["run_id"],
            "--context", self.identity["context"], "--evidence", str(path),
        ], env=self.env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.stored_state()["state"], "error")
        self.assertEqual(json.loads(result.stdout)["state"], "error")
        self.assertNotIn("Traceback", result.stderr)
        self.assertNotIn(str(self.root), result.stdout + result.stderr)

    def test_inner_invalid_timestamp_types_raise_normalized_validation_error(self):
        outer, inner, spec_record = self.inner_command_fixture()
        for field in ("started_at", "finished_at"):
            original = inner[field]
            for value in (None, 0, True, [], {}, "not-a-time"):
                inner[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.reporter.validate_inner_command(self.plan, outer, inner, spec_record)
            inner[field] = original

    def test_dockerfile_copy_parser_retains_all_current_non_tmp_files(self):
        self.assertTrue(hasattr(self.reporter, "dockerfile_copy_mappings"), "Dockerfile copy parser missing")
        raw = (ROOT / "Dockerfile").read_bytes()
        sources = {path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*") if path.is_file()}
        mappings = self.reporter.dockerfile_copy_mappings(raw, sources)
        self.assertEqual(len(mappings), 15)
        self.assertIn(("scripts/entrypoint.sh", "/usr/local/bin/entrypoint.sh"), mappings)
        self.assertIn(("s6-overlay/s6-rc.d/paperclip/run", "/etc/s6-overlay/s6-rc.d/paperclip/run"), mappings)
        self.assertFalse(any(destination.startswith("/tmp/") for _, destination in mappings))

    def test_dockerfile_copy_parser_rejects_unsupported_or_ambiguous_forms(self):
        self.assertTrue(hasattr(self.reporter, "dockerfile_copy_mappings"), "Dockerfile copy parser missing")
        for instruction in (
            'COPY ["input.txt", "/input.txt"]', "COPY --from=builder input.txt /input.txt",
            "COPY *.txt /files/", "COPY input.txt second.txt /files/", "COPY input.txt /files/",
            "COPY missing.txt /missing.txt", "COPY --link input.txt /input.txt",
            "COPY input.txt ../outside", "COPY input.txt /tmp/../retained.txt",
            "COPY input.txt \\\n /input.txt", "ADD input.txt /input.txt",
            "COPY input.txt /input.txt\nFROM scratch\nCOPY second.txt /second.txt",
        ):
            with self.subTest(instruction=instruction), self.assertRaises(ValueError):
                self.reporter.dockerfile_copy_mappings(("FROM scratch\n" + instruction + "\n").encode(),
                                                     {"input.txt", "second.txt"})


if __name__ == "__main__":
    unittest.main()
