#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, unquote


THIRD_PARTY_PURL_TYPES = {
    "apk",
    "cargo",
    "composer",
    "deb",
    "gem",
    "golang",
    "maven",
    "npm",
    "nuget",
    "pypi",
    "rpm",
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def exception_keys(record, release, platform, as_of):
    keys = set()
    errors = []
    if record.get("release") != release:
        errors.append(f"exception release must be {release}")
    if record.get("platform") != platform:
        errors.append(f"exception platform must be {platform}")
    if record.get("approvedBy") != "CoderLuii":
        errors.append("exception approvedBy must be CoderLuii")
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
                identifier = item.get("PkgIdentifier")
                if identifier is not None:
                    if not isinstance(identifier, dict):
                        return (
                            f"Trivy Results[{result_index}].{key}[{item_index}]"
                            ".PkgIdentifier must be an object"
                        )
                    if "PURL" in identifier and not isinstance(
                        identifier["PURL"], str
                    ):
                        return (
                            f"Trivy Results[{result_index}].{key}[{item_index}]"
                            ".PkgIdentifier.PURL must be a string"
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
                {
                    "kind": "vulnerability",
                    "vulnerability": item.get("VulnerabilityID", ""),
                    "package": item.get("PkgName", ""),
                    "installedVersion": item.get("InstalledVersion", ""),
                    "purl": item.get("PkgIdentifier", {}).get("PURL", ""),
                    "target": target,
                }
            )
        for item in result.get("Secrets") or []:
            findings.append(
                {
                    "kind": "secret",
                    "vulnerability": item.get("RuleID", "secret"),
                    "package": "secret",
                    "installedVersion": "",
                    "purl": "",
                    "target": item.get("Target") or target,
                }
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
                findings.append(
                    {
                        "kind": "vulnerability",
                        "vulnerability": cve,
                        "package": "",
                        "installedVersion": "",
                        "purl": "",
                        "target": "SARIF result without package metadata",
                    }
                )
                continue
            for purl in purls:
                parsed = parse_purl(purl)
                findings.append(
                    {
                        "kind": "vulnerability",
                        "vulnerability": cve,
                        "package": parsed[2] if parsed else "",
                        "installedVersion": parsed[3] if parsed else "",
                        "purl": purl,
                        "target": purl,
                    }
                )
    return findings


def parse_purl(value):
    purl = unquote(value)
    if not purl.startswith("pkg:"):
        return None
    purl_body = purl[4:].split("#", 1)[0]
    package_version, _, query = purl_body.partition("?")
    if "/" not in package_version or "@" not in package_version:
        return None
    package_path, version = package_version.rsplit("@", 1)
    package_type, path = package_path.split("/", 1)
    path_parts = [part for part in path.split("/") if part]
    if not package_type or not path_parts or not version:
        return None
    namespace = "/".join(path_parts[:-1])
    epoch = (parse_qs(query).get("epoch") or [""])[0]
    if epoch:
        version = f"{epoch}:{version}"
    return package_type.lower(), namespace, path_parts[-1], version


def project_owned_package(package, namespace):
    values = [package, *namespace.split("/")]
    normalized = {value.lower().lstrip("@").replace("_", "-") for value in values}
    return (
        "coderluii" in normalized
        or any(value == "holycode" or value.startswith("holycode-") for value in normalized)
    )


def classify_upstream_finding(finding):
    if finding["kind"] == "secret":
        return "secret finding"
    required = (
        finding["vulnerability"],
        finding["package"],
        finding["installedVersion"],
        finding["purl"],
    )
    if not all(isinstance(value, str) and value.strip() for value in required):
        return "unclassified finding"
    parsed = parse_purl(finding["purl"])
    if not parsed:
        return "unclassified finding"
    package_type, namespace, purl_package, purl_version = parsed
    if package_type not in THIRD_PARTY_PURL_TYPES:
        return "unclassified finding"
    if purl_version != finding["installedVersion"]:
        return "unclassified finding"
    reported_package = finding["package"].lower().lstrip("@")
    purl_names = {
        purl_package.lower().lstrip("@"),
        "/".join(value for value in (namespace, purl_package) if value)
        .lower()
        .lstrip("@"),
    }
    if reported_package not in purl_names:
        return "unclassified finding"
    if project_owned_package(finding["package"], namespace):
        return "project-owned finding"
    return None


def write_accepted_findings(path, scanner, release, platform, as_of, findings):
    record = {
        "release": release,
        "platform": platform,
        "scanner": scanner,
        "asOf": as_of.isoformat(),
        "policy": "accepted upstream vulnerabilities",
        "findings": [
            {
                "vulnerability": finding["vulnerability"],
                "package": finding["package"],
                "installedVersion": finding["installedVersion"],
                "purl": finding["purl"],
            }
            for finding in findings
        ],
    }
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scanner", choices=("scout", "trivy"), required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--exceptions", type=Path)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--release", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--accept-upstream-vulnerabilities", action="store_true")
    parser.add_argument("--accepted-findings", type=Path)
    args = parser.parse_args()

    if args.accept_upstream_vulnerabilities and not args.accepted_findings:
        parser.error("--accepted-findings is required with --accept-upstream-vulnerabilities")
    if args.accept_upstream_vulnerabilities and args.exceptions:
        parser.error("--exceptions cannot be combined with --accept-upstream-vulnerabilities")

    try:
        report = load_json(args.report)
        as_of = date.fromisoformat(args.as_of)
        record = (
            load_json(args.exceptions)
            if args.exceptions
            else {
                "release": args.release,
                "platform": args.platform,
                "approvedBy": "CoderLuii",
                "exceptions": [],
            }
        )
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

    allowed, errors = exception_keys(record, args.release, args.platform, as_of)
    findings = (
        scout_findings(report)
        if args.scanner == "scout"
        else trivy_findings(report)
    )
    if args.accept_upstream_vulnerabilities:
        blocked = []
        for finding in findings:
            reason = classify_upstream_finding(finding)
            if reason:
                blocked.append((reason, finding))
        for reason, finding in blocked:
            print(
                f"{reason}: {finding['vulnerability']} "
                f"{finding['package']}@{finding['installedVersion']} "
                f"({finding['target']})",
                file=sys.stderr,
            )
        if blocked:
            return 1
        try:
            write_accepted_findings(
                args.accepted_findings,
                args.scanner,
                args.release,
                args.platform,
                as_of,
                findings,
            )
        except OSError as error:
            print(error, file=sys.stderr)
            return 2
        print(f"accepted {len(findings)} upstream {args.scanner} finding(s)")
        return 0

    unexcepted = [
        finding
        for finding in findings
        if (
            finding["vulnerability"],
            finding["package"],
            finding["installedVersion"],
        ) not in allowed
    ]
    for error in errors:
        print(error, file=sys.stderr)
    for finding in unexcepted:
        print(
            f"unexcepted {args.scanner} finding: "
            f"{finding['vulnerability']} "
            f"{finding['package']}@{finding['installedVersion']} "
            f"({finding['target']})",
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
