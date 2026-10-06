import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WorkflowSecurityPolicyTests(unittest.TestCase):
    def test_pin_validator_enforces_upstream_vulnerability_evidence_policy(self):
        validator = (ROOT / "scripts" / "validate_workflow_pins.py").read_text(
            encoding="utf-8"
        )
        for value in (
            "--accept-upstream-vulnerabilities",
            "--accepted-findings",
            "scout-accepted.json",
            "trivy-accepted.json",
            "Validate Chromium security floor and refreshed availability",
        ):
            with self.subTest(value=value):
                self.assertIn(value, validator)
        self.assertIn("USE_ARM64_CHROMIUM_EXCEPTION", validator)
        self.assertIn("config/security-exceptions-v1.2.4.json", validator)


if __name__ == "__main__":
    unittest.main()
