import unittest
from pathlib import Path

from scripts.validate_workflow_pins import collect_errors


ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataTests(unittest.TestCase):
    def test_workflow_validator_accepts_current_release_metadata(self):
        self.assertEqual([], collect_errors())

    def test_previous_image_and_version_match_released_baseline(self):
        publish = (ROOT / ".github/workflows/docker-publish.yml").read_text()
        self.assertIn("PREVIOUS_VERSION: v1.2.0", publish)
        self.assertIn("RELEASE_VERSION: v1.2.1", publish)
        self.assertIn(
            "PREVIOUS_IMAGE: coderluii/holycode:1.2.0@sha256:"
            "72085db834a1ac2de07629abfeb8c9972296a40f3a0903fbd35d54155553f1c6",
            publish,
        )

    def test_validation_runtime_and_renovate_are_synchronized(self):
        for name in ("pr-validation.yml", "docker-publish.yml"):
            with self.subTest(workflow=name):
                workflow = (ROOT / ".github/workflows" / name).read_text()
                self.assertIn("node-version: 24.21.0", workflow)
                self.assertIn(
                    "bash scripts/validate_renovate_extraction.sh 44.87.1", workflow
                )
        extraction = (ROOT / "scripts/validate_renovate_extraction.sh").read_text()
        self.assertIn('renovate_version="${1:-44.87.1}"', extraction)


if __name__ == "__main__":
    unittest.main()
