import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_security_exceptions.py"


def valid_record():
    return {
        "release": "v1.1.4",
        "reviewDate": "2026-07-29",
        "exceptions": [
            {
                "cve": "CVE-2026-16804",
                "package": "chromium",
                "installedVersion": "150.0.7871.181-1~deb13u1",
                "fixedVersion": "150.0.7871.186",
                "availableVersion": "150.0.7871.181-1~deb13u1",
                "approvedSource": "Debian Trixie security",
                "reason": "The fixed Debian package is not published for Trixie.",
                "reachability": "Chromium opens content requested by the container user.",
                "controls": [
                    "Chromium runs as the unprivileged opencode user.",
                    "The setuid sandbox and constrained seccomp profile remain enabled.",
                ],
                "expires": "2026-08-28",
                "removalTrigger": "Upgrade when Debian Trixie publishes Chromium 150.0.7871.186 or newer.",
            }
        ],
    }


class SecurityExceptionTests(unittest.TestCase):
    def run_validator(self, record, *extra_args):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "exceptions.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--file",
                    str(path),
                    "--release",
                    "v1.1.4",
                    "--as-of",
                    "2026-07-29",
                    *extra_args,
                ],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_accepts_complete_unexpired_exception(self):
        result = self.run_validator(
            valid_record(),
            "--installed",
            "chromium=150.0.7871.181-1~deb13u1",
            "--available",
            "chromium=150.0.7871.181-1~deb13u1",
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_expired_exception(self):
        record = valid_record()
        record["exceptions"][0]["expires"] = "2026-07-28"
        result = self.run_validator(
            record,
            "--installed",
            "chromium=150.0.7871.181-1~deb13u1",
            "--available",
            "chromium=150.0.7871.181-1~deb13u1",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expired", result.stderr)

    def test_rejects_wildcards_and_missing_fields(self):
        record = valid_record()
        record["exceptions"][0]["cve"] = "CVE-*"
        del record["exceptions"][0]["controls"]
        result = self.run_validator(
            record,
            "--installed",
            "chromium=150.0.7871.181-1~deb13u1",
            "--available",
            "chromium=150.0.7871.181-1~deb13u1",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("controls", result.stderr)
        self.assertIn("wildcard", result.stderr)

    def test_rejects_exception_longer_than_thirty_days(self):
        record = valid_record()
        record["exceptions"][0]["expires"] = "2026-08-29"
        result = self.run_validator(
            record,
            "--installed",
            "chromium=150.0.7871.181-1~deb13u1",
            "--available",
            "chromium=150.0.7871.181-1~deb13u1",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("30 days", result.stderr)

    def test_rejects_exception_when_fixed_candidate_is_available(self):
        result = self.run_validator(
            valid_record(),
            "--installed",
            "chromium=150.0.7871.181-1~deb13u1",
            "--available",
            "chromium=150.0.7871.186-1~deb13u1",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("compatible fix is available", result.stderr)

    def test_rejects_missing_candidate_versions(self):
        result = self.run_validator(valid_record())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--installed", result.stderr)
        self.assertIn("--available", result.stderr)

    def test_rejects_installed_version_mismatch(self):
        result = self.run_validator(
            valid_record(),
            "--installed",
            "chromium=150.0.7871.124-1~deb13u1",
            "--available",
            "chromium=150.0.7871.181-1~deb13u1",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("installedVersion", result.stderr)


if __name__ == "__main__":
    unittest.main()
