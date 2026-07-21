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
    "actions/checkout": ("3d3c42e5aac5ba805825da76410c181273ba90b1", "v7.0.1"),
    "actions/upload-artifact": ("043fb46d1a93c77aae656e7c1c64a875d1fc6a0a", "v7.0.1"),
    "docker/setup-qemu-action": ("96fe6ef7f33517b61c61be40b68a1882f3264fb8", "v4.2.0"),
    "docker/setup-buildx-action": ("bb05f3f5519dd87d3ba754cc423b652a5edd6d2c", "v4.2.0"),
    "docker/login-action": ("af1e73f918a031802d376d3c8bbc3fe56130a9b0", "v4.4.0"),
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
            "actions/upload-artifact",
            "docker/setup-qemu-action",
            "docker/setup-buildx-action",
            "docker/login-action",
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
        "runner: ubuntu-24.04",
        "runner: ubuntu-24.04-arm",
        "SCOUT_VERSION: 1.23.1",
        "scout_sha256: 0f778f9d833f28bc6cccff95e33039849c0afcecafa38d9f46fe74bfd0915714",
        "scout_sha256: 88eecb7273f19bd18300d70e6f85b2e7d784e9e4f3cbb4a2b400db6b8355a52a",
        "docker/scout-cli/releases/download/v${SCOUT_VERSION}",
        'docker-scout cves "sbom://$SCOUT_SBOM"',
        "version: v0.72.0",
        "PREVIOUS_IMAGE: coderluii/holycode:1.1.2@sha256:65740c4d8aa416217391f53de4be984ea9f8dfd5f10553dead94db402645b537",
        'ref: ${{ github.sha }}',
        "Pull exact candidate digest",
        "scripts/test_upgrade_rollback.sh",
    ):
        if required_text not in protected_text:
            errors.append(f"protected-validation.yml must contain {required_text!r}")
    if protected_text.count("scanners: vuln,secret") != 2:
        errors.append("protected-validation.yml must run both Trivy gates with vuln and secret scanners")
    if "trivyignores:" in protected_text:
        errors.append("protected-validation.yml must not bypass the fixable critical/high gate")
    if "eceasy/cli-proxy-api" in protected_text:
        errors.append("protected-validation.yml must not pull the removed CLIProxyAPI sidecar")

    pr_validation = WORKFLOWS / "pr-validation.yml"
    pr_text = pr_validation.read_text(encoding="utf-8")
    if "renovate@43.274.0 renovate-config-validator --strict renovate.json" not in pr_text:
        errors.append("pr-validation.yml must validate renovate.json with the audited Renovate pin")

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
