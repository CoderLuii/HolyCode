#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import date
from pathlib import Path
from urllib.parse import unquote


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def exception_keys(record, as_of):
    keys = set()
    errors = []
    for item in record.get("exceptions", []):
        try:
            expires = date.fromisoformat(item["expires"])
            key = (item["cve"], item["package"], item["installedVersion"])
        except (KeyError, TypeError, ValueError) as error:
            errors.append(f"invalid exception record: {error}")
            continue
        if expires < as_of:
            errors.append(f"{item['cve']} exception expired on {expires.isoformat()}")
            continue
        keys.add(key)
    return keys, errors


def trivy_findings(report):
    findings = []
    for result in report.get("Results") or []:
        target = result.get("Target", "unknown target")
        for item in result.get("Vulnerabilities") or []:
            findings.append(
                (
                    item.get("VulnerabilityID", ""),
                    item.get("PkgName", ""),
                    item.get("InstalledVersion", ""),
                    target,
                )
            )
        for item in result.get("Secrets") or []:
            findings.append(
                (
                    item.get("RuleID", "secret"),
                    "secret",
                    "",
                    item.get("Target") or target,
                )
            )
    return findings


def scout_findings(report):
    findings = []
    for run in report.get("runs") or []:
        rules = {
            rule.get("id"): rule
            for rule in run.get("tool", {}).get("driver", {}).get("rules", [])
        }
        for result in run.get("results") or []:
            cve = result.get("ruleId", "")
            rule = rules.get(cve, {})
            purls = rule.get("properties", {}).get("purls") or []
            if not purls:
                findings.append((cve, "", "", "SARIF result without package metadata"))
                continue
            for purl in purls:
                package, version = parse_purl(purl)
                findings.append((cve, package, version, purl))
    return findings


def parse_purl(value):
    purl = unquote(value)
    package_version = purl.split("?", 1)[0].split("#", 1)[0]
    if "@" not in package_version:
        return package_version.rsplit("/", 1)[-1], ""
    package_path, version = package_version.rsplit("@", 1)
    return package_path.rsplit("/", 1)[-1], version


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scanner", choices=("scout", "trivy"), required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--exceptions", type=Path)
    parser.add_argument("--as-of", required=True)
    args = parser.parse_args()

    try:
        report = load_json(args.report)
        as_of = date.fromisoformat(args.as_of)
        record = load_json(args.exceptions) if args.exceptions else {"exceptions": []}
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(error, file=sys.stderr)
        return 2

    allowed, errors = exception_keys(record, as_of)
    findings = (
        scout_findings(report)
        if args.scanner == "scout"
        else trivy_findings(report)
    )
    unexcepted = [finding for finding in findings if finding[:3] not in allowed]
    for error in errors:
        print(error, file=sys.stderr)
    for cve, package, version, target in unexcepted:
        print(
            f"unexcepted {args.scanner} finding: "
            f"{cve} {package}@{version} ({target})",
            file=sys.stderr,
        )
    if errors or unexcepted:
        return 1

    print(
        f"validated {len(findings)} {args.scanner} finding(s): "
        f"{len(findings) - len(unexcepted)} excepted, 0 unexcepted"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
