#!/usr/bin/env python3
"""Check the exact main-branch source before qualification or publication."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

from validate_version import VersionError, validate_version


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"},
        text=True, stderr=subprocess.PIPE, timeout=30,
    ).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("validate", "release"), required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--main-ref", default="origin/main")
    parser.add_argument("--version", required=True)
    parser.add_argument("--previous-version", required=True)
    args = parser.parse_args()
    try:
        if not re.fullmatch(r"[0-9a-f]{40}", args.sha) or git("rev-parse", "HEAD") != args.sha:
            raise ValueError("checkout must match the exact requested SHA")
        if git("rev-parse", args.main_ref) != args.sha:
            raise ValueError("requested SHA must be the current main tip")
        git("merge-base", "--is-ancestor", args.previous_version, args.sha)
        title = git("log", "-1", "--format=%s", args.sha) if args.mode == "release" else None
        validate_version(args.version, args.previous_version, commit_title=title)
    except (ValueError, VersionError, subprocess.SubprocessError) as error:
        print(f"release source validation failed: {error}", file=sys.stderr)
        return 1
    print(f"Validated {args.mode} source {args.sha} for {args.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
