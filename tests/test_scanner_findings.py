import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_scanner_findings.py"


def exception_record(expires="2026-08-28"):
    return {
        "release": "v1.1.4",
        "reviewDate": "2026-07-30",
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
                "controls": ["Chromium runs sandboxed as opencode."],
                "expires": expires,
                "removalTrigger": "Upgrade when Debian publishes the fixed package.",
            }
        ],
    }


def trivy_report(cve="CVE-2026-16804", package="chromium", version="150.0.7871.181-1~deb13u1"):
    return {
        "Results": [
            {
                "Target": "holycode",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": cve,
                        "PkgName": package,
                        "InstalledVersion": version,
                        "FixedVersion": "150.0.7871.186",
                        "Severity": "HIGH",
                    }
                ],
            }
        ]
    }


def scout_report(cve="CVE-2026-16804", package="chromium", version="150.0.7871.181-1~deb13u1"):
    return {
        "runs": [
            {
                "tool": {
                    "driver": {
                        "rules": [
                            {
                                "id": cve,
                                "properties": {
                                    "purls": [f"pkg:deb/debian/{package}@{version}"]
                                },
                            }
                        ]
                    }
                },
                "results": [{"ruleId": cve, "message": {"text": "fixable"}}],
            }
        ]
    }


class ScannerFindingTests(unittest.TestCase):
    def run_validator(self, scanner, report, exceptions=None, as_of="2026-07-30"):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            report_path = temp / "report.json"
            exceptions_path = temp / "exceptions.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            exceptions_path.write_text(
                json.dumps(exceptions or exception_record()), encoding="utf-8"
            )
            return subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--scanner",
                    scanner,
                    "--report",
                    str(report_path),
                    "--exceptions",
                    str(exceptions_path),
                    "--as-of",
                    as_of,
                ],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_accepts_exact_trivy_exception(self):
        result = self.run_validator("trivy", trivy_report())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 excepted", result.stdout)

    def test_accepts_exact_scout_exception(self):
        result = self.run_validator("scout", scout_report())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 excepted", result.stdout)

    def test_rejects_unexcepted_finding(self):
        result = self.run_validator(
            "trivy", trivy_report(cve="CVE-2026-99999", package="other")
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexcepted", result.stderr)

    def test_rejects_package_or_version_mismatch(self):
        result = self.run_validator("trivy", trivy_report(package="chromium-common"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexcepted", result.stderr)

        result = self.run_validator(
            "scout", scout_report(version="150.0.7871.124-1~deb13u1")
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexcepted", result.stderr)

    def test_rejects_expired_exception(self):
        result = self.run_validator(
            "trivy",
            trivy_report(),
            exception_record(expires="2026-07-29"),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expired", result.stderr)

    def test_accepts_empty_reports(self):
        result = self.run_validator("trivy", {"Results": []})
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_validator("scout", {"runs": [{"results": []}]})
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
