import unittest

from scripts.validate_version import VersionError, validate_version


class ValidateVersionTests(unittest.TestCase):
    def test_accepts_v1_1_0_with_legacy_flag(self):
        validate_version(
            "v1.1.0",
            "v1.0.13",
            commit_title="v1.1.0",
            tag_name="v1.1.0",
            release_title="v1.1.0",
            allow_legacy_v1_0_13_to_v1_1_0=True,
        )

    def test_accepts_standard_rollovers(self):
        cases = [
            ("v1.1.4", "v1.1.5"),
            ("v1.0.9", "v1.1.0"),
            ("v1.1.9", "v1.2.0"),
            ("v1.9.9", "v2.0.0"),
        ]
        for previous, current in cases:
            with self.subTest(previous=previous, current=current):
                validate_version(current, previous)

    def test_rejects_two_digit_segments(self):
        for version in ("v1.0.10", "v1.1.10"):
            with self.subTest(version=version):
                with self.assertRaises(VersionError):
                    validate_version(version)

    def test_rejects_skipped_rollover(self):
        with self.assertRaises(VersionError):
            validate_version("v1.2.0", "v1.0.9")

    def test_rejects_mismatched_commit_tag_and_release_titles(self):
        mismatch_cases = [
            {"commit_title": "release v1.1.0"},
            {"tag_name": "v1.1.1"},
            {"release_title": "HolyCode v1.1.0"},
        ]
        for kwargs in mismatch_cases:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(VersionError):
                    validate_version("v1.1.0", "v1.0.13", allow_legacy_v1_0_13_to_v1_1_0=True, **kwargs)

    def test_rejects_legacy_bridge_without_explicit_flag(self):
        with self.assertRaises(VersionError):
            validate_version("v1.1.0", "v1.0.13")


if __name__ == "__main__":
    unittest.main()
