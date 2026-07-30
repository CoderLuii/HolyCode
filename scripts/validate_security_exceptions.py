#!/usr/bin/env python3
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path


REQUIRED_FIELDS = {
    "cve",
    "package",
    "installedVersion",
    "fixedVersion",
    "availableVersion",
    "approvedSource",
    "reason",
    "reachability",
    "controls",
    "expires",
    "removalTrigger",
}


def parse_date(value, field, errors):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        errors.append(f"{field} must use YYYY-MM-DD")
        return None


def version_key(value):
    numbers = re.findall(r"\d+", value)
    return tuple(int(number) for number in numbers[:4])


def validate(record, release, as_of, installed, available):
    errors = []
    if record.get("release") != release:
        errors.append(f"release must be {release}")

    review_date = parse_date(record.get("reviewDate"), "reviewDate", errors)
    if review_date and review_date > as_of:
        errors.append("reviewDate cannot be in the future")
    exceptions = record.get("exceptions")
    if not isinstance(exceptions, list) or not exceptions:
        errors.append("exceptions must be a non-empty list")
        return errors

    seen = set()
    for index, exception in enumerate(exceptions):
        label = f"exceptions[{index}]"
        if not isinstance(exception, dict):
            errors.append(f"{label} must be an object")
            continue

        missing = sorted(REQUIRED_FIELDS - exception.keys())
        for field in missing:
            errors.append(f"{label}.{field} is required")

        cve = exception.get("cve", "")
        package = exception.get("package", "")
        if cve in seen:
            errors.append(f"{label}.cve duplicates {cve}")
        seen.add(cve)
        if not re.fullmatch(r"CVE-\d{4}-\d{4,}", cve):
            errors.append(f"{label}.cve must name one exact CVE; wildcard values are not allowed")

        controls = exception.get("controls")
        if not isinstance(controls, list) or not controls or not all(
            isinstance(control, str) and control.strip() for control in controls
        ):
            errors.append(f"{label}.controls must be a non-empty list of concrete controls")

        for field, value in exception.items():
            values = value if isinstance(value, list) else [value]
            if any(isinstance(item, str) and "*" in item for item in values):
                errors.append(f"{label}.{field} contains a wildcard")

        expires = parse_date(exception.get("expires"), f"{label}.expires", errors)
        if review_date and expires:
            lifetime = (expires - review_date).days
            if lifetime < 0:
                errors.append(f"{label}.expires is before reviewDate")
            if lifetime > 30:
                errors.append(f"{label}.expires exceeds 30 days")
            if expires < as_of:
                errors.append(f"{label} expired on {expires.isoformat()}")

        recorded_available = exception.get("availableVersion", "")
        recorded_installed = exception.get("installedVersion", "")
        supplied_installed = installed.get(package)
        supplied_available = available.get(package)
        if not supplied_installed:
            errors.append(f"{label} has no candidate --installed value for {package}")
        elif supplied_installed != recorded_installed:
            errors.append(
                f"{label}.installedVersion is {recorded_installed}, "
                f"but validation found {supplied_installed}"
            )
        if not supplied_available:
            errors.append(f"{label} has no refreshed --available value for {package}")
        elif supplied_available != recorded_available:
            errors.append(
                f"{label}.availableVersion is {recorded_available}, "
                f"but validation found {supplied_available}"
            )
        fixed_version = exception.get("fixedVersion", "")
        if supplied_available and version_key(supplied_available) >= version_key(fixed_version):
            errors.append(
                f"{label} is invalid because a compatible fix is available: "
                f"{package} {supplied_available}"
            )

    return errors


def parse_available(values):
    available = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"invalid --available value: {value}")
        package, version = value.split("=", 1)
        if not package or not version:
            raise ValueError(f"invalid --available value: {value}")
        available[package] = version
    return available


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--release", required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--installed", action="append", default=[])
    parser.add_argument("--available", action="append", default=[])
    args = parser.parse_args()

    try:
        record = json.loads(args.file.read_text(encoding="utf-8"))
        as_of = date.fromisoformat(args.as_of)
        installed = parse_available(args.installed)
        available = parse_available(args.available)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(error, file=sys.stderr)
        return 2

    errors = validate(record, args.release, as_of, installed, available)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(
        f"validated {len(record['exceptions'])} security exception(s) "
        f"for {args.release}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
