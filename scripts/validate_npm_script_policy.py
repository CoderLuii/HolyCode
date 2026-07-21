#!/usr/bin/env python3
"""Validate npm lifecycle scripts in globally installed packages."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

LIFECYCLE_SCRIPTS = ("preinstall", "install", "postinstall")
INTEGRITY_PATTERN = re.compile(r"^sha512-[A-Za-z0-9+/]+={0,2}$")


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def is_package_root(package_json: Path) -> bool:
    package_dir = package_json.parent
    if package_dir.parent.name == "node_modules":
        return True
    return (
        package_dir.parent.name.startswith("@")
        and package_dir.parent.parent.name == "node_modules"
    )


def registry_integrity(package_id: str) -> str:
    return subprocess.check_output(
        ["npm", "view", package_id, "dist.integrity"],
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--target-arch", required=True, choices=("amd64", "arm64"))
    args = parser.parse_args()

    policy = load_json(args.policy)
    installed_npm = subprocess.check_output(["npm", "--version"], text=True).strip()
    installed_arch = subprocess.check_output(
        ["node", "-p", "process.arch"], text=True
    ).strip()
    errors: list[str] = []

    expected_node_arch = {"amd64": "x64", "arm64": "arm64"}[args.target_arch]
    if installed_arch != expected_node_arch:
        errors.append(
            f"target architecture {args.target_arch!r} does not match Node {installed_arch!r}"
        )

    if policy.get("npmVersion") != installed_npm:
        errors.append(
            f"policy npmVersion {policy.get('npmVersion')!r} does not match installed {installed_npm!r}"
        )
    if policy.get("mode") != "deny-by-default":
        errors.append("policy mode must be deny-by-default")

    allowed = policy.get("allowScripts")
    blocked = policy.get("blockedScripts")
    if not isinstance(allowed, dict) or not isinstance(blocked, dict):
        errors.append("allowScripts and blockedScripts must be objects")
        allowed = allowed if isinstance(allowed, dict) else {}
        blocked = blocked if isinstance(blocked, dict) else {}

    expected: dict[str, dict] = {}
    active_decisions = {"allowed": 0, "blocked": 0}
    for decision, entries in (("allowed", allowed), ("blocked", blocked)):
        for package_id, entry in entries.items():
            architectures = entry.get("architectures")
            if not isinstance(architectures, list) or not architectures:
                errors.append(f"{decision} entry {package_id} has no architectures")
                continue
            if any(arch not in ("amd64", "arm64") for arch in architectures):
                errors.append(
                    f"{decision} entry {package_id} has invalid architectures {architectures!r}"
                )
                continue
            if args.target_arch not in architectures:
                continue
            active_decisions[decision] += 1
            scripts = entry.get("scripts")
            reason = entry.get("reason")
            integrity = entry.get("integrity")
            if not isinstance(scripts, dict) or not scripts:
                errors.append(f"{decision} entry {package_id} has no scripts")
                continue
            if not isinstance(reason, str) or not reason.strip():
                errors.append(f"{decision} entry {package_id} has no reason")
            if not isinstance(integrity, str) or not INTEGRITY_PATTERN.fullmatch(integrity):
                errors.append(f"{decision} entry {package_id} has no valid SHA-512 integrity")
                continue
            expected[package_id] = {"scripts": scripts, "integrity": integrity}

    discovered: dict[str, dict[str, str]] = {}
    for package_json in args.root.rglob("package.json"):
        if not is_package_root(package_json):
            continue
        try:
            package = load_json(package_json)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        name = package.get("name")
        version = package.get("version")
        scripts = package.get("scripts")
        if not isinstance(name, str) or not isinstance(version, str) or not isinstance(scripts, dict):
            continue
        lifecycle = {
            key: scripts[key]
            for key in LIFECYCLE_SCRIPTS
            if isinstance(scripts.get(key), str)
        }
        if not lifecycle:
            continue
        package_id = f"{name}@{version}"
        previous = discovered.setdefault(package_id, lifecycle)
        if previous != lifecycle:
            errors.append(f"conflicting scripts discovered for {package_id}")

    for package_id in sorted(discovered.keys() - expected.keys()):
        errors.append(f"unreviewed lifecycle scripts: {package_id} {discovered[package_id]}")
    for package_id in sorted(expected.keys() - discovered.keys()):
        errors.append(f"policy entry is not installed: {package_id}")
    for package_id in sorted(discovered.keys() & expected.keys()):
        expected_scripts = expected[package_id]["scripts"]
        if discovered[package_id] != expected_scripts:
            errors.append(
                f"script mismatch for {package_id}: expected {expected_scripts}, "
                f"found {discovered[package_id]}"
            )
        try:
            actual_integrity = registry_integrity(package_id)
        except subprocess.CalledProcessError as error:
            errors.append(
                f"could not resolve registry integrity for {package_id}: {error.output.strip()}"
            )
            continue
        if actual_integrity != expected[package_id]["integrity"]:
            errors.append(
                f"integrity mismatch for {package_id}: expected "
                f"{expected[package_id]['integrity']}, found {actual_integrity}"
            )

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(
        f"npm {installed_npm}: reviewed {len(discovered)} lifecycle-script packages; "
        f"allowed {active_decisions['allowed']}, "
        f"blocked {active_decisions['blocked']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
