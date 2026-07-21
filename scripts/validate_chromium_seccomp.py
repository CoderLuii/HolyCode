#!/usr/bin/env python3
"""Validate the vendored Chromium sandbox seccomp profile."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "config" / "chromium-seccomp.json"
EXPECTED_SHA256 = "cc3e61cabda6bbc1e53e54d27ba4d55a9d3be829b6dd1a596f4a7b31b1cc7849"


def main() -> int:
    content = PROFILE.read_bytes()
    actual = hashlib.sha256(content).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"Chromium seccomp profile SHA-256 mismatch: {actual}")

    profile = json.loads(content)
    if profile.get("defaultAction") != "SCMP_ACT_ERRNO":
        raise SystemExit("Chromium seccomp profile must deny unlisted syscalls")

    namespace_rule = profile.get("syscalls", [{}])[0]
    if namespace_rule.get("action") != "SCMP_ACT_ALLOW" or set(
        namespace_rule.get("names", [])
    ) != {"clone", "setns", "unshare"}:
        raise SystemExit("Chromium seccomp profile namespace rule changed")

    print("Chromium seccomp profile validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
