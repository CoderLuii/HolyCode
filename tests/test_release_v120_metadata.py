import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataTests(unittest.TestCase):
    def test_previous_image_and_version_match_released_baseline(self):
        publish = (ROOT / ".github/workflows/docker-publish.yml").read_text()
        self.assertIn("PREVIOUS_VERSION: v1.1.9", publish)
        self.assertIn("RELEASE_VERSION: v1.2.0", publish)
        self.assertIn(
            "PREVIOUS_IMAGE: coderluii/holycode:1.1.9@sha256:"
            "06344a7b42b4938959c8913687d57a1fbbf65a18a11864bab3fca95d3b9b801c",
            publish,
        )

    def test_validation_runtime_and_renovate_are_synchronized(self):
        for name in ("pr-validation.yml", "docker-publish.yml"):
            with self.subTest(workflow=name):
                workflow = (ROOT / ".github/workflows" / name).read_text()
                self.assertIn("node-version: 24.21.0", workflow)
                self.assertIn(
                    "bash scripts/validate_renovate_extraction.sh 44.79.2", workflow
                )
        extraction = (ROOT / "scripts/validate_renovate_extraction.sh").read_text()
        self.assertIn('renovate_version="${1:-44.79.2}"', extraction)


if __name__ == "__main__":
    unittest.main()
