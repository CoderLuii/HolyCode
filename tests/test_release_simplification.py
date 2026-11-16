import re
import unittest
from pathlib import Path



ROOT = Path(__file__).resolve().parents[1]


class ReleaseSimplificationTests(unittest.TestCase):
    def job(self, source, name):
        match = re.search(rf"(?ms)^  {name}:\n(.*?)(?=^  [a-z][a-z-]*:|\Z)", source)
        self.assertIsNotNone(match)
        return match.group(1)

    def test_validation_is_default_and_cannot_promote_or_update_description(self):
        source = (ROOT / ".github/workflows/docker-publish.yml").read_text(encoding="utf-8")
        inputs = source.split("concurrency:", 1)[0]
        self.assertIn("default: validate", inputs)
        self.assertRegex(inputs, r"options:\n\s+- validate\n\s+- release\n")
        self.assertNotIn("release_version:", inputs)
        for name in ("promote-candidate", "update-dockerhub-description"):
            self.assertIn("if: inputs.mode == 'release'", self.job(source, name))
        self.assertRegex(source, r"Require unpublished image aliases and a matching draft\n\s+if: inputs.mode == 'release'")
        self.assertNotIn("commit_count", source)

    def test_development_workflow_does_not_rebuild_release_images(self):
        source = (ROOT / ".github/workflows/pr-validation.yml").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"(?m)^  ([a-z][a-z-]*):$", source.split("jobs:\n", 1)[1]), ["static-validation"])
        self.assertNotIn("docker build", source)
        self.assertNotIn("packages: write", source)

    def test_every_scanner_and_native_runtime_gate_stays_in_release(self):
        source = (ROOT / ".github/workflows/docker-publish.yml").read_text(encoding="utf-8")
        protected = self.job(source, "protected-validation")
        for platform in ("linux/amd64", "linux/arm64"):
            self.assertIn("platform: " + platform, protected)
        for name in ("Smoke test tools and Chromium sandbox", "Validate offline plugin modes", "Validate Hermes migration guard",
                     "Validate upgrade, persistence, and rollback", "Trivy vulnerability report",
                     "Trivy fixable critical and high gate", "Docker Scout vulnerability reports",
                     "Enforce protected scanner gates"):
            self.assertIn("- name: " + name, protected)

    def test_chromium_check_uses_one_container_and_repository_refresh(self):
        source = (ROOT / "scripts/check_chromium_packages.sh").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"\bdocker run\b", source)), 1)
        self.assertEqual(source.count("apt-get update"), 1)
        self.assertIn("--interactive", source)
        for package in ("chromium", "chromium-common", "chromium-sandbox"):
            self.assertIn(package, source)
        self.assertIn("validate-holycode-chromium-version", source)
        self.assertIn('dpkg --compare-versions "$installed" ge "$available"', source)

    def test_scanner_cache_is_shared_within_one_architecture_but_not_between_them(self):
        source = (ROOT / ".github/workflows/docker-publish.yml").read_text(encoding="utf-8")
        protected = self.job(source, "protected-validation")
        blocks = re.split(r"(?m)^      - name: ", protected)
        scanners = [block for block in blocks if "uses: aquasecurity/trivy-action@" in block]
        self.assertEqual(len(scanners), 3)
        paths = []
        for block in scanners:
            match = re.search(r"(?m)^          cache-dir: (.+)$", block)
            self.assertIsNotNone(match, "Each scanner must select an architecture-specific cache")
            paths.append(match.group(1))
        rendered = {arch: {path.replace("${{ matrix.suffix }}", arch) for path in paths}
                    for arch in ("amd64", "arm64")}
        self.assertEqual(len(rendered["amd64"]), 1)
        self.assertEqual(len(rendered["arm64"]), 1)
        self.assertTrue(rendered["amd64"].isdisjoint(rendered["arm64"]))


if __name__ == "__main__":
    unittest.main()
