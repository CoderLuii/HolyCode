#!/usr/bin/env python3
"""Validate immutable action pins and release-workflow guardrails."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
USES_RE = re.compile(r"^\s*uses:\s*([^@\s]+)@([^\s#]+)(?:\s*#\s*(\S+))?\s*$")

REQUIRED_PINS = {
    "actions/checkout": ("9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0", "v7.0.0"),
    "docker/setup-qemu-action": ("96fe6ef7f33517b61c61be40b68a1882f3264fb8", "v4.2.0"),
    "docker/setup-buildx-action": ("bb05f3f5519dd87d3ba754cc423b652a5edd6d2c", "v4.2.0"),
    "docker/login-action": ("af1e73f918a031802d376d3c8bbc3fe56130a9b0", "v4.4.0"),
    "docker/metadata-action": ("dc802804100637a589fabce1cb79ff13a1411302", "v6.2.0"),
    "docker/build-push-action": ("53b7df96c91f9c12dcc8a07bcb9ccacbed38856a", "v7.3.0"),
    "peter-evans/dockerhub-description": ("1b9a80c056b620d92cedb9d9b5a223409c68ddfa", "v5.0.0"),
    "aquasecurity/trivy-action": ("ed142fd0673e97e23eac54620cfb913e5ce36c25", "v0.36.0"),
}


def collect_errors() -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()

    for workflow in sorted(WORKFLOWS.glob("*.yml")):
        text = workflow.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            match = USES_RE.match(line)
            if not match:
                continue
            action, ref, version_comment = match.groups()
            location = f"{workflow.relative_to(ROOT)}:{line_number}"
            if not SHA_RE.fullmatch(ref):
                errors.append(f"{location} uses {action}@{ref}; external actions must be pinned to a 40-char SHA")
                continue
            if action in REQUIRED_PINS:
                expected_ref, expected_version = REQUIRED_PINS[action]
                seen.add(action)
                if ref != expected_ref:
                    errors.append(f"{location} uses {action}@{ref}; expected {expected_ref}")
                if version_comment != expected_version:
                    errors.append(f"{location} must keep comment '# {expected_version}'")

    docker_publish = WORKFLOWS / "docker-publish.yml"
    publish_text = docker_publish.read_text(encoding="utf-8")
    if "workflow_dispatch:" in publish_text:
        errors.append("docker-publish.yml must not expose workflow_dispatch; manual runs can overwrite latest")
    if "GHCR_TOKEN" in publish_text:
        errors.append("docker-publish.yml must use secrets.GITHUB_TOKEN for GHCR, not a separate GHCR_TOKEN")
    if "packages: write" not in publish_text or "contents: read" not in publish_text:
        errors.append("docker-publish.yml must declare minimal contents/packages permissions")

    missing_required = {
        action
        for action in (
            "actions/checkout",
            "docker/setup-qemu-action",
            "docker/setup-buildx-action",
            "docker/login-action",
            "docker/metadata-action",
            "docker/build-push-action",
            "peter-evans/dockerhub-description",
            "aquasecurity/trivy-action",
        )
        if action not in seen
    }
    for action in sorted(missing_required):
        errors.append(f"required pinned action is not present: {action}")

    protected_validation = WORKFLOWS / "protected-validation.yml"
    protected_text = protected_validation.read_text(encoding="utf-8")
    for required_text in (
        "workflow_call:",
        "workflow_dispatch:",
        "SCOUT_VERSION: 1.23.1",
        "SCOUT_SHA256: 0f778f9d833f28bc6cccff95e33039849c0afcecafa38d9f46fe74bfd0915714",
        "docker/scout-cli/releases/download/v${SCOUT_VERSION}",
        'docker-scout cves "sbom://$SCOUT_SBOM"',
        "version: v0.72.0",
        "trivyignores: .trivyignore.yaml",
        "scripts/test_upgrade_rollback.sh",
    ):
        if required_text not in protected_text:
            errors.append(f"protected-validation.yml must contain {required_text!r}")
    if protected_text.count("scanners: vuln,secret") != 2:
        errors.append("protected-validation.yml must run both Trivy gates with vuln and secret scanners")

    return errors


def main() -> int:
    errors = collect_errors()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("workflow pin validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
