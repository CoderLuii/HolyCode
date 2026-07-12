#!/usr/bin/env python3
"""Validate HolyCode release versions and release-title alignment."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass


VERSION_RE = re.compile(r"^v([0-9])\.([0-9])\.([0-9])$")
LEGACY_PREVIOUS = "v1.0.13"
LEGACY_CURRENT = "v1.1.0"


class VersionError(ValueError):
    pass


@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> "Version":
        match = VERSION_RE.fullmatch(value)
        if not match:
            raise VersionError(
                f"{value!r} does not match required release pattern ^v[0-9]\\.[0-9]\\.[0-9]$"
            )
        return cls(*(int(part) for part in match.groups()))

    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}.{self.patch}"

    def next(self) -> "Version":
        if self.patch < 9:
            return Version(self.major, self.minor, self.patch + 1)
        if self.minor < 9:
            return Version(self.major, self.minor + 1, 0)
        return Version(self.major + 1, 0, 0)


def validate_version(
    version: str,
    previous_version: str | None = None,
    *,
    commit_title: str | None = None,
    tag_name: str | None = None,
    release_title: str | None = None,
    allow_legacy_v1_0_13_to_v1_1_0: bool = False,
) -> None:
    current = Version.parse(version)

    expected_titles = {
        "commit title": commit_title,
        "tag name": tag_name,
        "release title": release_title,
    }
    for label, value in expected_titles.items():
        if value is not None and value != version:
            raise VersionError(f"{label} {value!r} must exactly match {version!r}")

    if not previous_version:
        return

    if (
        allow_legacy_v1_0_13_to_v1_1_0
        and previous_version == LEGACY_PREVIOUS
        and version == LEGACY_CURRENT
    ):
        return

    if previous_version == LEGACY_PREVIOUS and version == LEGACY_CURRENT:
        raise VersionError(
            f"{LEGACY_PREVIOUS} to {LEGACY_CURRENT} requires --allow-legacy-v1-0-13-to-v1-1-0"
        )

    previous = Version.parse(previous_version)
    expected = previous.next()
    if current != expected:
        raise VersionError(f"{version!r} must be the next release after {previous_version!r}: expected {expected}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Release version to validate, for example v1.1.0")
    parser.add_argument("--previous-version", help="Previous release version")
    parser.add_argument("--commit-title", help="Commit subject/title that must exactly match --version")
    parser.add_argument("--tag-name", help="Git tag name that must exactly match --version")
    parser.add_argument("--release-title", help="GitHub release title that must exactly match --version")
    parser.add_argument(
        "--allow-legacy-v1-0-13-to-v1-1-0",
        action="store_true",
        help="Allow the one-time bridge from historical v1.0.13 to strict v1.1.0",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        validate_version(
            args.version,
            args.previous_version,
            commit_title=args.commit_title,
            tag_name=args.tag_name,
            release_title=args.release_title,
            allow_legacy_v1_0_13_to_v1_1_0=args.allow_legacy_v1_0_13_to_v1_1_0,
        )
    except VersionError as exc:
        print(f"version validation failed: {exc}", file=sys.stderr)
        return 1

    print(f"version validation passed: {args.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
