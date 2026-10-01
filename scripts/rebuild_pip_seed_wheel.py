#!/usr/bin/env python3
"""Repack the verified pip wheel with HolyCode's repaired vendored bytes."""

import argparse
import hashlib
import shutil
import tempfile
import zipfile
from pathlib import Path

if __package__:
    from scripts.verify_pip_vendor_record import VENDORS, refresh_record, verify_record
else:
    from verify_pip_vendor_record import VENDORS, refresh_record, verify_record


PIP_WHEEL_SHA256 = "71138adf1f4ca900cdb7d289c21b7494329f2332b6d85f0e1c42108c0384ed3e"
INFO_NAME = "pip-26.2.1.dist-info"


def rebuild(source: Path, installed_site: Path, output: Path) -> None:
    if hashlib.sha256(source.read_bytes()).hexdigest() != PIP_WHEEL_SHA256:
        raise ValueError("upstream pip wheel SHA256 mismatch")
    with tempfile.TemporaryDirectory(prefix="holycode-pip-wheel-") as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(source) as archive:
            archive.extractall(root)
        info = root / INFO_NAME
        installed_info = installed_site / INFO_NAME
        for name in VENDORS:
            relative = Path("pip") / "_vendor" / name
            shutil.rmtree(root / relative)
            shutil.copytree(installed_site / relative, root / relative,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            license_relative = Path("licenses") / "src" / "pip" / "_vendor" / name
            shutil.rmtree(info / license_relative)
            shutil.copytree(installed_info / license_relative, info / license_relative)
        for name in ("vendor.txt", "bom.cdx.json"):
            shutil.copy2(installed_site / "pip" / "_vendor" / name,
                         root / "pip" / "_vendor" / name)
        refresh_record(root, info)
        verify_record(root, info)
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=9) as archive:
            for file in sorted(root.rglob("*")):
                if not file.is_file():
                    continue
                member = zipfile.ZipInfo(file.relative_to(root).as_posix(),
                                         date_time=(1980, 1, 1, 0, 0, 0))
                member.compress_type = zipfile.ZIP_DEFLATED
                member.external_attr = 0o100644 << 16
                archive.writestr(member, file.read_bytes(), compress_type=zipfile.ZIP_DEFLATED,
                                 compresslevel=9)
    print(hashlib.sha256(output.read_bytes()).hexdigest())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("installed_site", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rebuild(args.source, args.installed_site, args.output)
