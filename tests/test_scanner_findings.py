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
        "platform": "linux/arm64",
        "approvedBy": "CoderLuii",
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


def trivy_report(
    cve="CVE-2026-16804",
    package="chromium",
    version="150.0.7871.181-1~deb13u1",
    purl=None,
):
    if purl is None:
        purl = f"pkg:deb/debian/{package}@{version}"
    return {
        "Results": [
            {
                "Target": "holycode",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": cve,
                        "PkgName": package,
                        "InstalledVersion": version,
                        "PkgIdentifier": {"PURL": purl},
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
    def run_validator(
        self, scanner, report, exceptions=None, as_of="2026-07-30", use_exceptions=True
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            report_path = temp / "report.json"
            exceptions_path = temp / "exceptions.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            exceptions_path.write_text(
                json.dumps(exceptions or exception_record()), encoding="utf-8"
            )
            command = [
                sys.executable,
                str(VALIDATOR),
                "--scanner",
                scanner,
                "--report",
                str(report_path),
                "--as-of",
                as_of,
                "--release",
                "v1.1.4",
                "--platform",
                "linux/arm64",
            ]
            if use_exceptions:
                command.extend(("--exceptions", str(exceptions_path)))
            return subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

    def run_advisory_validator(self, scanner, report):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            report_path = temp / "report.json"
            accepted_path = temp / "accepted.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--scanner",
                    scanner,
                    "--report",
                    str(report_path),
                    "--as-of",
                    "2026-10-05",
                    "--release",
                    "v1.2.5",
                    "--platform",
                    "linux/arm64",
                    "--accept-upstream-vulnerabilities",
                    "--accepted-findings",
                    str(accepted_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            accepted = (
                json.loads(accepted_path.read_text(encoding="utf-8"))
                if accepted_path.is_file()
                else None
            )
            return result, accepted

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

    def test_rejects_exception_on_wrong_release_or_platform(self):
        for field, value in (
            ("release", "v1.2.4"),
            ("platform", "linux/amd64"),
        ):
            with self.subTest(field=field):
                record = exception_record()
                record[field] = value
                result = self.run_validator("trivy", trivy_report(), record)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(field, result.stderr)

    def test_accepts_empty_reports(self):
        result = self.run_validator("trivy", {"Results": []})
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_validator("scout", {"runs": [{"results": []}]})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_reports_without_the_scanner_collection(self):
        for scanner in ("trivy", "scout"):
            with self.subTest(scanner=scanner):
                result = self.run_validator(scanner, {})
                self.assertEqual(result.returncode, 2)
                self.assertIn("invalid scanner report", result.stderr)

    def test_rejects_cross_scanner_reports(self):
        cases = (
            ("trivy", {"runs": [{"results": []}]}),
            ("scout", {"Results": []}),
        )
        for scanner, report in cases:
            with self.subTest(scanner=scanner):
                result = self.run_validator(scanner, report)
                self.assertEqual(result.returncode, 2)
                self.assertIn("invalid scanner report", result.stderr)

    def test_rejects_wrong_scanner_collection_types(self):
        cases = (
            ("trivy", []),
            ("trivy", {"Results": {}}),
            ("trivy", {"Results": [[]]}),
            ("trivy", {"Results": [{"Vulnerabilities": {}}]}),
            ("trivy", {"Results": [{"Secrets": {}}]}),
            ("scout", []),
            ("scout", {"runs": {}}),
            ("scout", {"runs": []}),
            ("scout", {"runs": [[]]}),
            ("scout", {"runs": [{"results": {}}]}),
        )
        for scanner, report in cases:
            with self.subTest(scanner=scanner, report=report):
                result = self.run_validator(scanner, report)
                self.assertEqual(result.returncode, 2)
                self.assertIn("invalid scanner report", result.stderr)

    def test_rejects_wrong_scout_nested_structure_types(self):
        reports = (
            {"runs": [{"results": [], "tool": None}]},
            {"runs": [{"results": [], "tool": {"driver": []}}]},
            {"runs": [{"results": [], "tool": {"driver": {"rules": {}}}}]},
            {"runs": [{"results": [], "tool": {"driver": {"rules": [[]]}}}]},
            {
                "runs": [
                    {
                        "results": [],
                        "tool": {"driver": {"rules": [{"properties": []}]}},
                    }
                ]
            },
            {
                "runs": [
                    {
                        "results": [],
                        "tool": {
                            "driver": {"rules": [{"properties": {"purls": {}}}]}
                        },
                    }
                ]
            },
            {
                "runs": [
                    {
                        "results": [],
                        "tool": {
                            "driver": {"rules": [{"properties": {"purls": [1]}}]}
                        },
                    }
                ]
            },
        )
        for report in reports:
            with self.subTest(report=report):
                result = self.run_validator("scout", report)
                self.assertEqual(result.returncode, 2)
                self.assertIn("invalid scanner report", result.stderr)

    def test_rejects_non_string_scanner_key_fields(self):
        cases = []
        for invalid in ([], {}):
            for key in ("VulnerabilityID", "PkgName", "InstalledVersion"):
                cases.append(
                    (
                        "trivy",
                        {"Results": [{"Vulnerabilities": [{key: invalid}]}]},
                    )
                )
            cases.append(
                ("trivy", {"Results": [{"Secrets": [{"RuleID": invalid}]}]})
            )
            cases.append(
                (
                    "scout",
                    {
                        "runs": [
                            {
                                "tool": {"driver": {"rules": [{"id": invalid}]}},
                                "results": [],
                            }
                        ]
                    },
                )
            )
            cases.append(
                (
                    "scout",
                    {
                        "runs": [
                            {
                                "tool": {"driver": {"rules": []}},
                                "results": [{"ruleId": invalid}],
                            }
                        ]
                    },
                )
            )
        for scanner, report in cases:
            with self.subTest(scanner=scanner, report=report):
                result = self.run_validator(scanner, report)
                self.assertEqual(result.returncode, 2)
                self.assertIn("invalid scanner report", result.stderr)

    def test_no_exception_mode_accepts_empty_report(self):
        result = self.run_validator(
            "trivy", {"Results": []}, use_exceptions=False
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_no_exception_mode_rejects_finding(self):
        result = self.run_validator(
            "trivy", trivy_report(), use_exceptions=False
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexcepted", result.stderr)

    def test_advisory_mode_records_validated_third_party_findings(self):
        for scanner, report in (
            ("trivy", trivy_report()),
            ("scout", scout_report()),
        ):
            with self.subTest(scanner=scanner):
                result, accepted = self.run_advisory_validator(scanner, report)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(accepted["release"], "v1.2.5")
                self.assertEqual(accepted["platform"], "linux/arm64")
                self.assertEqual(accepted["scanner"], scanner)
                self.assertEqual(accepted["asOf"], "2026-10-05")
                self.assertEqual(
                    accepted["findings"],
                    [
                        {
                            "vulnerability": "CVE-2026-16804",
                            "package": "chromium",
                            "installedVersion": "150.0.7871.181-1~deb13u1",
                            "purl": "pkg:deb/debian/chromium@150.0.7871.181-1~deb13u1",
                        }
                    ],
                )
                self.assertIn("accepted 1 upstream", result.stdout)

    def test_advisory_mode_matches_debian_epoch_qualifier(self):
        report = trivy_report(
            package="bsdutils",
            version="1:2.41.5-0+deb13u1",
            purl=(
                "pkg:deb/debian/bsdutils@2.41.5-0%2Bdeb13u1"
                "?arch=amd64&distro=debian-13.7&epoch=1"
            ),
        )
        result, accepted = self.run_advisory_validator("trivy", report)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            accepted["findings"][0]["installedVersion"],
            "1:2.41.5-0+deb13u1",
        )

    def test_advisory_mode_rejects_secrets(self):
        report = {
            "Results": [
                {
                    "Target": "rootfs",
                    "Secrets": [{"RuleID": "private-key", "Target": "/app/key"}],
                }
            ]
        }
        result, accepted = self.run_advisory_validator("trivy", report)
        self.assertEqual(result.returncode, 1)
        self.assertIsNone(accepted)
        self.assertIn("secret finding", result.stderr)

    def test_advisory_mode_rejects_missing_or_unrecognized_package_provenance(self):
        reports = (
            trivy_report(purl=""),
            trivy_report(purl="pkg:generic/vendor/chromium@150.0.7871.181"),
            scout_report(package="chromium", version=""),
        )
        for report in reports:
            scanner = "trivy" if "Results" in report else "scout"
            with self.subTest(scanner=scanner, report=report):
                result, accepted = self.run_advisory_validator(scanner, report)
                self.assertEqual(result.returncode, 1)
                self.assertIsNone(accepted)
                self.assertIn("unclassified finding", result.stderr)

    def test_advisory_mode_rejects_project_owned_packages(self):
        for scanner, report in (
            (
                "trivy",
                trivy_report(
                    package="holycode",
                    version="1.2.5",
                    purl="pkg:npm/%40coderluii/holycode@1.2.5",
                ),
            ),
            (
                "scout",
                scout_report(
                    package="holycode",
                    version="1.2.5",
                ),
            ),
            (
                "scout",
                scout_report(
                    package="holycode-utils",
                    version="1.2.5",
                ),
            ),
        ):
            with self.subTest(scanner=scanner):
                result, accepted = self.run_advisory_validator(scanner, report)
                self.assertEqual(result.returncode, 1)
                self.assertIsNone(accepted)
                self.assertIn("project-owned finding", result.stderr)

    def test_advisory_mode_requires_an_evidence_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "report.json"
            report_path.write_text(json.dumps(trivy_report()), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--scanner",
                    "trivy",
                    "--report",
                    str(report_path),
                    "--as-of",
                    "2026-10-05",
                    "--release",
                    "v1.2.5",
                    "--platform",
                    "linux/amd64",
                    "--accept-upstream-vulnerabilities",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--accepted-findings", result.stderr)


if __name__ == "__main__":
    unittest.main()
