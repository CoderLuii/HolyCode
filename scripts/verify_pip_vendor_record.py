#!/usr/bin/env python3
"""Refresh or verify pip's RECORD for HolyCode's three vendored repairs."""

import argparse
import base64
import csv
import hashlib
import importlib.metadata
import importlib.util
from pathlib import Path


VENDORS = ("msgpack", "pkg_resources", "urllib3")
METADATA = ("pip/_vendor/vendor.txt", "pip/_vendor/bom.cdx.json")


def tracked_files(site: Path, info: Path) -> set[str]:
    paths = set(METADATA)
    for name in VENDORS:
        for root in (
            site / "pip" / "_vendor" / name,
            info / "licenses" / "src" / "pip" / "_vendor" / name,
        ):
            if not root.is_dir():
                continue
            for file in root.rglob("*"):
                if file.is_file() and "__pycache__" not in file.parts:
                    paths.add(file.relative_to(site).as_posix())
    return paths


def is_repaired_path(path: str, info: Path) -> bool:
    if path in METADATA:
        return True
    return any(
        path.startswith(f"pip/_vendor/{name}/")
        or path.startswith(f"{info.name}/licenses/src/pip/_vendor/{name}/")
        for name in VENDORS
    )


def digest(file: Path) -> tuple[str, str]:
    data = file.read_bytes()
    encoded = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
    return f"sha256={encoded.decode('ascii')}", str(len(data))


def read_record(info: Path) -> dict[str, tuple[str, str]]:
    with (info / "RECORD").open(newline="") as stream:
        return {path: (hash_value, size) for path, hash_value, size in csv.reader(stream)}


def refresh_record(site: Path, info: Path) -> None:
    rows = {
        path: values
        for path, values in read_record(info).items()
        if not is_repaired_path(path, info)
    }
    for path in tracked_files(site, info):
        file = site / path
        if not file.is_file():
            raise ValueError(f"missing pip vendor file: {path}")
        rows[path] = digest(file)
    rows[f"{info.name}/RECORD"] = ("", "")
    with (info / "RECORD").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerows((path, *rows[path]) for path in sorted(rows))


def verify_record(site: Path, info: Path) -> None:
    rows = read_record(info)
    expected = tracked_files(site, info)
    generated = {
        Path(importlib.util.cache_from_source(str(site / path))).relative_to(site).as_posix()
        for path in expected
        if path.endswith(".py")
    }
    for path in rows.keys() & generated:
        if rows[path] != ("", "") or not (site / path).is_file():
            raise ValueError(f"invalid pip vendor bytecode RECORD entry: {path}")
    recorded = {path for path in rows if is_repaired_path(path, info) and path not in generated}
    if recorded != expected:
        raise ValueError(f"pip vendor RECORD path mismatch: {sorted(recorded ^ expected)}")
    for path in expected:
        if rows[path] != digest(site / path):
            raise ValueError(f"pip vendor RECORD digest mismatch: {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    distribution = importlib.metadata.distribution("pip")
    info_path = Path(distribution._path)
    site_path = info_path.parent
    if args.refresh:
        refresh_record(site_path, info_path)
    verify_record(site_path, info_path)
