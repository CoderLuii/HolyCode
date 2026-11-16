import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReleaseSourceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull,
                    "GIT_CONFIG_SYSTEM": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.commit("v1.2.9")
        self.git("tag", "v1.2.9")
        self.commit("README update")

    def git(self, *args):
        result = subprocess.run(["git", *args], cwd=self.root, env=self.env,
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def commit(self, title):
        (self.root / "content").write_text(title, encoding="utf-8")
        self.git("add", "content")
        self.git("commit", "-m", title)

    def check(self, mode="validate", sha=None, version="v1.3.0"):
        return subprocess.run(
            [sys.executable, "-B", str(ROOT / "scripts/validate_release_source.py"),
             "--mode", mode, "--sha", sha or self.git("rev-parse", "HEAD"),
             "--main-ref", "main", "--version", version,
             "--previous-version", "v1.2.9"],
            cwd=self.root, env=self.env, capture_output=True, text=True, timeout=15,
        )

    def test_validation_accepts_documentation_commit_without_release_title(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_release_accepts_intervening_commits(self):
        self.commit("v1.3.0")
        result = self.check("release")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_release_rejects_wrong_title(self):
        result = self.check("release")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("commit title", result.stderr)

    def test_rejects_wrong_sha_and_non_main_checkout(self):
        result = self.check(sha="0" * 40)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exact", result.stderr)
        self.git("checkout", "-b", "feature")
        self.commit("feature")
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("main", result.stderr)

    def test_rejects_invalid_version_and_missing_predecessor(self):
        self.assertNotEqual(self.check(version="v1.3.1").returncode, 0)
        self.git("tag", "-d", "v1.2.9")
        self.assertNotEqual(self.check().returncode, 0)


if __name__ == "__main__":
    unittest.main()
