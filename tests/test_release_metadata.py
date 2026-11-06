import unittest
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from scripts import validate_workflow_pins
from scripts.validate_workflow_pins import collect_errors


ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataTests(unittest.TestCase):
    def test_workflow_validator_accepts_current_release_metadata(self):
        self.assertEqual([], collect_errors())

    def test_previous_image_and_version_match_released_baseline(self):
        publish = (ROOT / ".github/workflows/docker-publish.yml").read_text()
        self.assertIn("PREVIOUS_VERSION: v1.2.9", publish)
        self.assertIn("RELEASE_VERSION: v1.3.0", publish)
        self.assertIn(
            "PREVIOUS_IMAGE: coderluii/holycode:1.2.9@sha256:"
            "3d0bdce2a62f4eb6a5b03ec644b608d2c370da143474c6c6a81474ef1a16c439",
            publish,
        )

    def test_validator_rejects_a_different_image_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflows = root / ".github/workflows"
            shutil.copytree(ROOT / ".github/workflows", workflows)
            (root / "Dockerfile").write_text("ARG RELEASE_VERSION=v1.0.0\n")
            with patch.object(validate_workflow_pins, "ROOT", root), patch.object(
                validate_workflow_pins, "WORKFLOWS", workflows
            ):
                errors = collect_errors()
            self.assertTrue(
                any("Dockerfile release must match" in error for error in errors),
                errors,
            )

    def test_validation_runtime_and_renovate_are_synchronized(self):
        for name in ("pr-validation.yml", "docker-publish.yml"):
            with self.subTest(workflow=name):
                workflow = (ROOT / ".github/workflows" / name).read_text()
                self.assertIn("node-version: 24.22.2", workflow)
                self.assertIn(
                    "bash scripts/validate_renovate_extraction.sh 44.129.0", workflow
                )
        extraction = (ROOT / "scripts/validate_renovate_extraction.sh").read_text()
        self.assertIn('renovate_version="${1:-44.129.0}"', extraction)

    def test_docker_release_actions_use_the_audited_pins(self):
        publish = (ROOT / ".github/workflows/docker-publish.yml").read_text()
        for pin in (
            "docker/setup-buildx-action@f87e5991a6d7451dcb8d9637bfbc97413f497069 # v4.4.1",
            "docker/build-push-action@c3c9e263c25d99ce0380d002d59b67737d91b0dc # v7.4.0",
        ):
            with self.subTest(pin=pin):
                self.assertIn(pin, publish)
        self.assertNotIn("docker/setup-qemu-action@", publish)

    def test_optional_qemu_still_requires_its_audited_pin(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflows = root / ".github/workflows"
            shutil.copytree(ROOT / ".github/workflows", workflows)
            shutil.copyfile(ROOT / "Dockerfile", root / "Dockerfile")
            (workflows / "optional-emulation.yml").write_text(
                "on:\n  workflow_dispatch:\njobs:\n  optional:\n"
                "    runs-on: ubuntu-24.04\n    steps:\n"
                "      - name: Optional emulation\n"
                "        uses: docker/setup-qemu-action@" + "0" * 40 + " # v4.4.0\n"
            )
            with patch.object(validate_workflow_pins, "ROOT", root), patch.object(
                validate_workflow_pins, "WORKFLOWS", workflows
            ):
                errors = collect_errors()
            self.assertTrue(any("docker/setup-qemu-action@" in error and "expected" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
