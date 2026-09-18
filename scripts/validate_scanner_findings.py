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


def validate_trivy_report(report):
    if not isinstance(report, dict):
        return "top level must be an object"
    results = report.get("Results")
    if not isinstance(results, list):
        return "Trivy Results must be an array"
    for result_index, result in enumerate(results):
        if not isinstance(result, dict):
            return f"Trivy Results[{result_index}] must be an object"
        for key in ("Vulnerabilities", "Secrets"):
            if key not in result:
                continue
            items = result[key]
            if not isinstance(items, list):
                return f"Trivy Results[{result_index}].{key} must be an array"
            for item_index, item in enumerate(items):
                if not isinstance(item, dict):
                    return (
                        f"Trivy Results[{result_index}].{key}[{item_index}] "
                        "must be an object"
                    )
                fields = (
                    ("VulnerabilityID", "PkgName", "InstalledVersion")
                    if key == "Vulnerabilities"
                    else ("RuleID",)
                )
                for field in fields:
                    if field in item and not isinstance(item[field], str):
                        return (
                            f"Trivy Results[{result_index}].{key}[{item_index}]"
                            f".{field} must be a string"
                        )
    return None


def validate_scout_report(report):
    if not isinstance(report, dict):
        return "top level must be an object"
    runs = report.get("runs")
    if not isinstance(runs, list) or not runs:
        return "Scout runs must be a non-empty array"
    for run_index, run in enumerate(runs):
        if not isinstance(run, dict):
            return f"Scout runs[{run_index}] must be an object"
        results = run.get("results")
        if not isinstance(results, list):
            return f"Scout runs[{run_index}].results must be an array"
        for result_index, result in enumerate(results):
            if not isinstance(result, dict):
                return (
                    f"Scout runs[{run_index}].results[{result_index}] "
                    "must be an object"
                )
            if "ruleId" in result and not isinstance(result["ruleId"], str):
                return (
                    f"Scout runs[{run_index}].results[{result_index}].ruleId "
                    "must be a string"
                )
        tool = run.get("tool", {})
        if not isinstance(tool, dict):
            return f"Scout runs[{run_index}].tool must be an object"
        driver = tool.get("driver", {})
        if not isinstance(driver, dict):
            return f"Scout runs[{run_index}].tool.driver must be an object"
        rules = driver.get("rules", [])
        if not isinstance(rules, list):
            return f"Scout runs[{run_index}].tool.driver.rules must be an array"
        for rule_index, rule in enumerate(rules):
            if not isinstance(rule, dict):
                return (
                    f"Scout runs[{run_index}].tool.driver.rules[{rule_index}] "
                    "must be an object"
                )
            if "id" in rule and not isinstance(rule["id"], str):
                return (
                    f"Scout runs[{run_index}].tool.driver.rules[{rule_index}].id "
                    "must be a string"
                )
            properties = rule.get("properties", {})
            if not isinstance(properties, dict):
                return (
                    f"Scout runs[{run_index}].tool.driver.rules[{rule_index}]"
                    ".properties must be an object"
                )
            purls = properties.get("purls", [])
            if not isinstance(purls, list) or not all(
                isinstance(purl, str) for purl in purls
            ):
                return (
                    f"Scout runs[{run_index}].tool.driver.rules[{rule_index}]"
                    ".properties.purls must be an array of strings"
                )
    return None


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

    report_error = (
        validate_scout_report(report)
        if args.scanner == "scout"
        else validate_trivy_report(report)
    )
    if report_error:
        print(f"invalid scanner report: {report_error}", file=sys.stderr)
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
