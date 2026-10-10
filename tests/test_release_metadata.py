import unittest
from pathlib import Path

from scripts.validate_workflow_pins import collect_errors


ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataTests(unittest.TestCase):
    def test_workflow_validator_accepts_current_release_metadata(self):
        self.assertEqual([], collect_errors())

    def test_previous_image_and_version_match_released_baseline(self):
        publish = (ROOT / ".github/workflows/docker-publish.yml").read_text()
        self.assertIn("PREVIOUS_VERSION: v1.2.5", publish)
        self.assertIn("RELEASE_VERSION: v1.2.6", publish)
        self.assertIn(
            "PREVIOUS_IMAGE: coderluii/holycode:1.2.5@sha256:"
            "035b0d86aafd7cf52db7dbbbd9cb3ae53cc195a1aa0ab58843c2c2d3809eb9e3",
            publish,
        )

    def test_validation_runtime_and_renovate_are_synchronized(self):
        for name in ("pr-validation.yml", "docker-publish.yml"):
            with self.subTest(workflow=name):
                workflow = (ROOT / ".github/workflows" / name).read_text()
                self.assertIn("node-version: 24.21.0", workflow)
                self.assertIn(
                    "bash scripts/validate_renovate_extraction.sh 44.129.0", workflow
                )
        extraction = (ROOT / "scripts/validate_renovate_extraction.sh").read_text()
        self.assertIn('renovate_version="${1:-44.129.0}"', extraction)

    def test_docker_release_actions_use_the_audited_pins(self):
        publish = (ROOT / ".github/workflows/docker-publish.yml").read_text()
        for pin in (
            "docker/setup-qemu-action@99012661954931238ded8c8b007157a8430204e1 # v4.4.0",
            "docker/setup-buildx-action@f87e5991a6d7451dcb8d9637bfbc97413f497069 # v4.4.1",
            "docker/build-push-action@c3c9e263c25d99ce0380d002d59b67737d91b0dc # v7.4.0",
        ):
            with self.subTest(pin=pin):
                self.assertIn(pin, publish)


if __name__ == "__main__":
    unittest.main()
