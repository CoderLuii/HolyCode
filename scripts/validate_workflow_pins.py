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
    "actions/setup-node": ("820762786026740c76f36085b0efc47a31fe5020", "v7.0.0"),
    "actions/upload-artifact": ("043fb46d1a93c77aae656e7c1c64a875d1fc6a0a", "v7.0.1"),
    "docker/setup-qemu-action": ("96fe6ef7f33517b61c61be40b68a1882f3264fb8", "v4.2.0"),
    "docker/setup-buildx-action": ("bb05f3f5519dd87d3ba754cc423b652a5edd6d2c", "v4.2.0"),
    "docker/login-action": ("dbcb813823bdd20940b903addbd779551569679f", "v4.6.0"),
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
            "actions/setup-node",
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

    protected_text = publish_text
    for required_text in (
        "runner: ubuntu-24.04",
        "runner: ubuntu-24.04-arm",
        "SCOUT_VERSION: 1.24.0",
        "scout_sha256: f4e2814bd61040365153d5b964b144cb2dc6ee536a68b5bac4cadf00fc0ec34b",
        "scout_sha256: 8b21594c72d4d9403a82a49e9dbdfc04c27c6a21933906f1eefbb0beabe22d58",
        "trivy_sha256: 2edd39da482bb4e9831962487b68f68e3928ec3137794757f54d00383d79547b",
        "trivy_sha256: 13833d97e8a1a5367471c372a173180157f593bece570e20d5d925fef552f5dd",
        "docker/scout-cli/releases/download/v${SCOUT_VERSION}",
        "aquasecurity/trivy/releases/download/v${TRIVY_VERSION}",
        'docker-scout cves "sbom://$SCOUT_SBOM"',
        "version: v0.73.0",
        "PREVIOUS_IMAGE: coderluii/holycode:1.1.5@sha256:804ec668b97466dba9a26ded8af258fabc2d778047b7c8aebdaab7bccd9a3ae8",
        "PREVIOUS_VERSION: v1.1.6",
        "RELEASE_VERSION: v1.1.7",
        "python -m unittest discover -s tests",
        "python scripts/validate_workflow_pins.py",
        "python scripts/validate_chromium_seccomp.py",
        "bash scripts/validate_renovate_extraction.sh 44.24.2",
        "scripts/validate_scanner_findings.py",
        "bash scripts/test_plugin_modes.sh",
        'ref: ${{ github.sha }}',
        'git rev-parse origin/main',
        "Pull exact candidate digest",
        "scripts/test_upgrade_rollback.sh",
    ):
        if required_text not in protected_text:
            errors.append(f"docker-publish.yml must contain {required_text!r}")
    if protected_text.count("scanners: vuln,secret") != 2:
        errors.append("docker-publish.yml must run both Trivy gates with vuln and secret scanners")
    if protected_text.count("skip-setup-trivy: true") != 3:
        errors.append("docker-publish.yml must use the integrity-bound Trivy installation")
    if "trivyignores:" in protected_text:
        errors.append("docker-publish.yml must not bypass the fixable critical/high gate")
    if "eceasy/cli-proxy-api" in protected_text:
        errors.append("docker-publish.yml must not pull the removed CLIProxyAPI sidecar")
    if "config/security-exceptions-v1.1.4.json" in protected_text:
        errors.append("docker-publish.yml must not reuse the historical v1.1.4 exceptions")

    pr_validation = WORKFLOWS / "pr-validation.yml"
    pr_text = pr_validation.read_text(encoding="utf-8")
    for required_text in (
        "workflow_dispatch:",
        "if: github.event_name == 'workflow_dispatch'",
        "test \"$GITHUB_REF\" = 'refs/heads/main'",
        "runner: ubuntu-24.04",
        "runner: ubuntu-24.04-arm",
        "platform: linux/amd64",
        "platform: linux/arm64",
        "bash scripts/smoke_image.sh",
        "bash scripts/test_plugin_modes.sh",
        "scout_arch: amd64",
        "scout_arch: arm64",
        "scout_sha256: f4e2814bd61040365153d5b964b144cb2dc6ee536a68b5bac4cadf00fc0ec34b",
        "scout_sha256: 8b21594c72d4d9403a82a49e9dbdfc04c27c6a21933906f1eefbb0beabe22d58",
        "trivy_sha256: 2edd39da482bb4e9831962487b68f68e3928ec3137794757f54d00383d79547b",
        "trivy_sha256: 13833d97e8a1a5367471c372a173180157f593bece570e20d5d925fef552f5dd",
        "SCOUT_VERSION: 1.24.0",
        "TRIVY_VERSION: 0.73.0",
        "aquasecurity/trivy/releases/download/v${TRIVY_VERSION}",
        'docker-scout cves "sbom://$SCOUT_SBOM"',
        "--scanner scout",
        "--scanner trivy",
        "version: v0.73.0",
        "ignore-unfixed: true",
        "holycode-pretag-${{ github.sha }}-${{ matrix.suffix }}-evidence",
        "holycode-${{ matrix.suffix }}.commit-sha.txt",
        "holycode-${{ matrix.suffix }}.dpkg-inventory.txt",
        "holycode-${{ matrix.suffix }}.image-id.txt",
        "holycode-${{ matrix.suffix }}.scout-fixable.sarif",
        "holycode-${{ matrix.suffix }}.trivy-fixable.json",
        "SCOUT_GATE_OUTCOME: ${{ steps.scout_gate.outcome }}",
        "TRIVY_GATE_OUTCOME: ${{ steps.trivy_gate.outcome }}",
        'test "$SCOUT_GATE_OUTCOME" = "success"',
        'test "$TRIVY_GATE_OUTCOME" = "success"',
    ):
        if required_text not in pr_text:
            errors.append(f"pr-validation.yml must contain {required_text!r}")
    if "github.event_name == 'pull_request' || github.ref" in pr_text:
        errors.append("pr-validation.yml must fail rejected manual refs, not skip every job")
    if "bash scripts/validate_renovate_extraction.sh 44.24.2" not in pr_text:
        errors.append("pr-validation.yml must validate Renovate extraction with the audited pin")
    if pr_text.count("scanners: vuln,secret") != 2:
        errors.append("manual pre-tag validation must run both Trivy gates with vuln and secret scanners")
    if pr_text.count("skip-setup-trivy: true") != 3:
        errors.append("manual pre-tag validation must use the integrity-bound Trivy installation")
    manual_steps = (
        "Install Trivy CLI",
        "Generate pre-tag SPDX SBOM for Docker Scout",
        "Install Docker Scout CLI for pre-tag validation",
        "Login to Docker Hub for pre-tag Docker Scout",
        "Generate pre-tag Docker Scout vulnerability reports",
        "Docker Scout pre-tag fixable critical and high gate",
        "Generate pre-tag Trivy vulnerability report",
        "Trivy pre-tag fixable critical and high gate",
        "Validate pre-tag Trivy fixable critical and high findings",
        "Collect pre-tag architecture evidence",
        "Upload pre-tag architecture evidence",
        "Enforce pre-tag scanner gates",
    )
    for step_name in manual_steps:
        condition = re.compile(
            rf"- name: {re.escape(step_name)}\n"
            rf"(?:\s+id: [^\n]+\n)?"
            rf"\s+if: (?:always\(\) && )?github\.event_name == 'workflow_dispatch'"
        )
        if not condition.search(pr_text):
            errors.append(f"pr-validation.yml must limit {step_name!r} to manual runs")

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
