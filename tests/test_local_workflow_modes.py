import unittest
import copy
import json
import os
import re
import shutil
import subprocess
import tempfile
import textwrap
import sys
from pathlib import Path
from unittest.mock import patch

from scripts import validate_workflow_pins


ROOT = Path(__file__).resolve().parents[1]


class LocalWorkflowModeTests(unittest.TestCase):
    def publisher_job(self, name):
        workflow = (ROOT / ".github/workflows/docker-publish.yml").read_text(encoding="utf-8")
        match = re.search(rf"(?ms)^  {re.escape(name)}:\n(.*?)(?=^  [a-z][a-z0-9-]*:\n|\Z)", workflow)
        self.assertIsNotNone(match, f"Missing publisher job {name}")
        return match.group(1)

    def publisher_step(self, job, name):
        match = re.search(rf"(?ms)^      - name: {re.escape(name)}\n(.*?)(?=^      - name: |\Z)", job)
        self.assertIsNotNone(match, f"Missing publisher step {name}")
        return match.group(1)

    def bash(self):
        bash = "C:/Program Files/Git/bin/bash.exe" if os.name == "nt" else shutil.which("bash")
        if not bash or not Path(bash).is_file():
            self.skipTest("Bash is required to exercise workflow shell guards")
        return bash

    def check(self, source):
        validator = getattr(validate_workflow_pins, "manual_trigger_errors", None)
        self.assertIsNotNone(validator, "manual-only workflow policy is missing")
        return validator(source, "fixture.yml")

    def test_accepts_only_explicit_manual_event(self):
        self.assertEqual([], self.check("name: Fixture\non:\n  workflow_dispatch:\njobs: {}\n"))

    def test_rejects_automatic_events_beside_manual_event(self):
        for event in ("push", "pull_request", "release", "workflow_run", "schedule"):
            with self.subTest(event=event):
                self.assertTrue(self.check(f"on:\n  workflow_dispatch:\n  {event}:\njobs: {{}}\n"))

    def test_rejects_automatic_event_without_manual_event(self):
        self.assertTrue(self.check("on:\n  push:\n    tags: [v*]\njobs: {}\n"))

    def test_rejects_inline_event_forms_and_aliases(self):
        for source in ("on: push\n", "on: [push, workflow_dispatch]\n", "on: {push: null}\n", "on: *events\n"):
            with self.subTest(source=source):
                self.assertTrue(self.check(source))

    def test_rejects_missing_or_duplicate_event_block(self):
        self.assertTrue(self.check("name: Missing\njobs: {}\n"))
        self.assertTrue(self.check("on:\n  workflow_dispatch:\non:\n  push:\n"))

    def test_top_level_comment_cannot_hide_a_later_automatic_event(self):
        self.assertTrue(
            self.check("on:\n  workflow_dispatch:\n# still in the event mapping\n  push:\njobs: {}\n")
        )

    def test_rejects_quoted_event_keys_and_yaml_merges(self):
        for entry in ("'push':", '"pull_request":', "<<: *automatic"):
            with self.subTest(entry=entry):
                self.assertTrue(self.check(f"on:\n  workflow_dispatch:\n  {entry}\njobs: {{}}\n"))

    def test_rejects_quoted_and_escaped_duplicate_top_level_keys(self):
        for key in ("'on'", '"on"', '"\\u006f\\u006e"'):
            with self.subTest(key=key):
                self.assertTrue(self.check(f"on:\n  workflow_dispatch:\njobs: {{}}\n{key}: push\n"))

    def test_yaml_extension_is_checked_too(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflows = root / ".github/workflows"
            shutil.copytree(ROOT / ".github/workflows", workflows)
            shutil.copyfile(ROOT / "Dockerfile", root / "Dockerfile")
            (workflows / "automatic.yaml").write_text("on: push\njobs: {}\n")
            with patch.object(validate_workflow_pins, "ROOT", root), patch.object(
                validate_workflow_pins, "WORKFLOWS", workflows
            ):
                errors = validate_workflow_pins.collect_errors()
            self.assertTrue(any("automatic.yaml" in error for error in errors), errors)

    def test_comments_and_nested_input_names_do_not_become_events(self):
        source = "on:\n  # push is not an event here\n  workflow_dispatch:\n    inputs:\n      release:\n        type: string\n# pull_request:\njobs: {}\n"
        self.assertEqual([], self.check(source))

    def test_both_retained_workflows_have_no_automatic_event(self):
        for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
            with self.subTest(workflow=path.name):
                self.assertEqual([], self.check(path.read_text(encoding="utf-8")))

    def test_manual_main_run_uses_release_version_for_every_image_alias(self):
        bash = "C:/Program Files/Git/bin/bash.exe" if os.name == "nt" else shutil.which("bash")
        if not bash or not Path(bash).is_file():
            self.skipTest("Bash is required to exercise image-version expansion")
        workflow = (ROOT / ".github/workflows/docker-publish.yml").read_text(encoding="utf-8")
        assignments = re.findall(r'^\s*(version="[^"\n]+")\s*$', workflow, re.MULTILINE)
        self.assertEqual(len(assignments), 2, "Both registry-promotion commands must bind the version")
        for assignment in assignments:
            with self.subTest(assignment=assignment):
                result = subprocess.run(
                    [bash, "--noprofile", "--norc", "-c", assignment + '\nprintf "%s" "$version"'],
                    env={**os.environ, "GITHUB_REF_NAME": "main", "RELEASE_VERSION": "v1.3.0"},
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "1.3.0")

    def test_hosted_release_runs_static_once_and_builds_native_candidates_in_parallel(self):
        workflow = (ROOT / ".github/workflows/docker-publish.yml").read_text(encoding="utf-8")
        source = self.publisher_job("validate-source")
        build = self.publisher_job("build-candidate")
        compose = self.publisher_job("compose-candidate")
        protected = self.publisher_job("protected-validation")
        promotion = self.publisher_job("promote-candidate")
        for command in (
            "python -m unittest discover -s tests",
            "python scripts/validate_workflow_pins.py",
            "python scripts/validate_chromium_seccomp.py",
            "bash scripts/validate_renovate_extraction.sh 44.129.0",
        ):
            with self.subTest(command=command):
                self.assertEqual(workflow.count(command), 1)
                self.assertIn(command, source)
        self.assertLess(source.index("Verify Docker Hub credentials before native builds"), source.index("Static release validation"))
        self.assertIn("needs: validate-source", build)
        self.assertIn("runs-on: ${{ matrix.runner }}", build)
        self.assertIn("platforms: ${{ matrix.platform }}", build)
        self.assertRegex(build, r"platform: linux/amd64\n\s+suffix: amd64\n\s+runner: ubuntu-24.04\n")
        self.assertRegex(build, r"platform: linux/arm64\n\s+suffix: arm64\n\s+runner: ubuntu-24.04-arm\n")
        self.assertNotIn("max-parallel: 1", build)
        self.assertNotIn("docker/setup-qemu-action@", workflow)
        self.assertIn("sbom: true", build)
        self.assertIn("provenance: mode=max", build)
        self.assertEqual(workflow.count("docker/build-push-action@"), 1)
        self.assertIn("needs: build-candidate", compose)
        self.assertIn("needs: compose-candidate", protected)
        self.assertIn("CANDIDATE_DIGEST: ${{ needs.compose-candidate.outputs.digest }}", protected)
        self.assertIn("needs: release-validation", promotion)
        self.assertNotIn("report_local_status.py", workflow)

    def test_draft_guard_has_push_access_without_broadening_downstream_contents_permissions(self):
        for name, expected in (("validate-source", "write"), ("build-candidate", "read"),
                               ("compose-candidate", "read"), ("protected-validation", "read")):
            with self.subTest(job=name):
                job = self.publisher_job(name)
                block = re.search(r"(?ms)^    permissions:\n(.*?)(?=^    [a-z][a-z-]*:|\Z)", job)
                self.assertIsNotNone(block)
                permissions = dict(re.findall(r"(?m)^      ([a-z-]+): (read|write|none)(?:\s+#.*)?$", block.group(1)))
                self.assertEqual(permissions.get("contents"), expected)
        guard = self.publisher_step(self.publisher_job("validate-source"), "Require unpublished image aliases and a matching draft")
        self.assertIn("python scripts/check_release_target.py", guard)
        self.assertIn('--sha "$GITHUB_SHA" --require-draft', guard)

    def test_native_build_guard_rejects_a_runner_for_the_other_architecture(self):
        step = self.publisher_step(self.publisher_job("build-candidate"), "Require native build architecture")
        script = textwrap.dedent(step.split("        run: |\n", 1)[1])
        for arch in ("amd64", "arm64"):
            for machine in ("x86_64", "aarch64", "armv7l"):
                with self.subTest(arch=arch, machine=machine):
                    code = script.replace("${{ matrix.suffix }}", arch)
                    result = subprocess.run(
                        [self.bash(), "--noprofile", "--norc", "-c", 'uname() { printf "%s\\n" "$FIXTURE_MACHINE"; };\n' + code],
                        env={**os.environ, "FIXTURE_MACHINE": machine}, capture_output=True, text=True, timeout=15,
                    )
                    expected = (arch, machine) in (("amd64", "x86_64"), ("arm64", "aarch64"))
                    self.assertEqual(result.returncode == 0, expected, result.stderr)

    def test_native_artifact_layout_and_attestations_survive_composition(self):
        compose = self.publisher_job("compose-candidate")
        scripts = [textwrap.dedent(code) for code in re.findall(r"(?ms)python - <<'PY'\n(.*?)^          PY\n", compose)]
        self.assertEqual(len(scripts), 2)
        self.assertIn('--name "holycode-$RELEASE_VERSION-$arch-candidate"', compose)
        self.assertIn('--dir "candidate-inputs/$arch"', compose)
        self.assertIn('candidate-inputs/$arch/candidate-$arch.txt', compose)
        media = "application/vnd.oci.image.index.v1+json"
        for change in (None, "wrong-native-platform", "wrong-attestation-target", "lost-attestation", "wrong-combined-digest"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                members = []
                for arch, index_char, native_char, attestation_char in (("amd64", "a", "b", "c"), ("arm64", "d", "e", "f")):
                    digest = "sha256:" + index_char * 64
                    native = {"digest": "sha256:" + native_char * 64, "size": 123, "mediaType": "application/vnd.oci.image.manifest.v1+json", "platform": {"os": "linux", "architecture": arch}}
                    attestation = {"digest": "sha256:" + attestation_char * 64, "size": 456, "mediaType": "application/vnd.oci.image.manifest.v1+json", "platform": {"os": "unknown", "architecture": "unknown"}, "annotations": {"vnd.docker.reference.type": "attestation-manifest", "vnd.docker.reference.digest": native["digest"]}}
                    index = {"digest": digest, "schemaVersion": 2, "mediaType": media, "manifests": [native, attestation]}
                    members.extend(copy.deepcopy(index["manifests"]))
                    if arch == "arm64" and change == "wrong-native-platform":
                        native["platform"]["architecture"] = "amd64"
                    if arch == "arm64" and change == "wrong-attestation-target":
                        attestation["annotations"]["vnd.docker.reference.digest"] = "sha256:" + "0" * 64
                    target = root / "candidate-inputs" / arch
                    target.mkdir(parents=True)
                    (target / f"candidate-{arch}.txt").write_text(digest + "\n")
                    (root / f"candidate-{arch}.index.json").write_text(json.dumps(index))
                first = subprocess.run([sys.executable, "-B", "-c", scripts[0]], cwd=root, capture_output=True, text=True, timeout=15)
                if change in ("wrong-native-platform", "wrong-attestation-target"):
                    self.assertNotEqual(first.returncode, 0)
                    continue
                self.assertEqual(first.returncode, 0, first.stderr)
                digest = "sha256:" + "9" * 64
                metadata = {"digest": digest, "mediaType": media}
                combined = {"digest": digest, "schemaVersion": 2, "mediaType": media, "manifests": members}
                if change == "lost-attestation":
                    combined["manifests"].pop()
                if change == "wrong-combined-digest":
                    combined["digest"] = "sha256:" + "8" * 64
                (root / "candidate-metadata.json").write_text(json.dumps({"containerimage.descriptor": metadata}))
                (root / "candidate-index.json").write_text(json.dumps(combined))
                result = subprocess.run([sys.executable, "-B", "-c", scripts[1]], cwd=root, capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode == 0, change is None, result.stderr)

    def test_release_validation_blocks_failure_cancellation_or_skipped_prerequisites(self):
        job = self.publisher_job("release-validation")
        self.assertNotRegex(job, r"(?m)^    name: (?!release-validation$)")
        self.assertIn("if: always()", job)
        self.assertIn("needs: [validate-source, build-candidate, compose-candidate, protected-validation]", job)
        step = self.publisher_step(job, "Enforce release validation")
        script = textwrap.dedent(step.split("        run: |\n", 1)[1])
        inputs = dict(re.findall(r"(?m)^          ([A-Z_]+): \$\{\{ needs\.([a-z-]+)\.result \}\}$", step))
        self.assertEqual(set(inputs.values()), {"validate-source", "build-candidate", "compose-candidate", "protected-validation"})
        outcomes = [{name: "success" for name in inputs}]
        for name in inputs:
            for failed in ("failure", "cancelled", "skipped"):
                outcomes.append({**outcomes[0], name: failed})
        for values in outcomes:
            with self.subTest(values=values):
                result = subprocess.run([self.bash(), "--noprofile", "--norc", "-c", script], env={**os.environ, **values}, capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode == 0, all(value == "success" for value in values.values()), result.stderr)


if __name__ == "__main__":
    unittest.main()
