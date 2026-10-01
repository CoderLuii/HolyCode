import base64
import csv
import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts import rebuild_pip_seed_wheel


class RebuildPipSeedWheelTests(unittest.TestCase):
    def test_reproducible_repaired_wheel_keeps_unrelated_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            site = root / "site"
            info = "pip-26.2.1.dist-info"
            original = {
                "pip/__init__.py": b"unchanged pip entrypoint\n",
                f"{info}/entry_points.txt": b"[console_scripts]\npip=pip:main\n",
                "pip/_vendor/vendor.txt": b"    urllib3==2.7.0\n",
                "pip/_vendor/bom.cdx.json": b"{}\n",
            }
            for name in rebuild_pip_seed_wheel.VENDORS:
                package = f"pip/_vendor/{name}"
                license_path = f"{info}/licenses/src/pip/_vendor/{name}/LICENSE.txt"
                original[f"{package}/__init__.py"] = b"old\n"
                original[f"{package}/LICENSE.txt"] = b"old license\n"
                original[license_path] = b"old license\n"
                installed = site / package
                installed.mkdir(parents=True)
                (installed / "__init__.py").write_bytes(f"{name} repaired\n".encode())
                (installed / "LICENSE.txt").write_bytes(f"{name} license\n".encode())
                installed_license = site / license_path
                installed_license.parent.mkdir(parents=True)
                installed_license.write_bytes(f"{name} license\n".encode())
            (site / "pip/_vendor/vendor.txt").write_bytes(b"    urllib3==2.8.0\n")
            (site / "pip/_vendor/bom.cdx.json").write_bytes(b'{"components": []}\n')
            record = io.StringIO(newline="")
            writer = csv.writer(record)
            for name, data in original.items():
                digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
                writer.writerow((name, f"sha256={digest.decode()}", len(data)))
            writer.writerow((f"{info}/RECORD", "", ""))
            original[f"{info}/RECORD"] = record.getvalue().encode()
            source = root / "pip-26.2.1-py3-none-any.whl"
            with zipfile.ZipFile(source, "w") as archive:
                for name, data in original.items():
                    archive.writestr(name, data)
            first, second = root / "first.whl", root / "second.whl"
            with patch.object(rebuild_pip_seed_wheel, "PIP_WHEEL_SHA256",
                              hashlib.sha256(source.read_bytes()).hexdigest()):
                rebuild_pip_seed_wheel.rebuild(source, site, first)
                rebuild_pip_seed_wheel.rebuild(source, site, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(archive.read("pip/__init__.py"), original["pip/__init__.py"])
                self.assertEqual(archive.read(f"{info}/entry_points.txt"),
                                 original[f"{info}/entry_points.txt"])
                self.assertEqual(archive.read("pip/_vendor/urllib3/__init__.py"),
                                 b"urllib3 repaired\n")
                rows = csv.reader(io.StringIO(archive.read(f"{info}/RECORD").decode()))
                recorded_names = set()
                for name, recorded_hash, recorded_size in rows:
                    recorded_names.add(name)
                    if name == f"{info}/RECORD":
                        self.assertEqual((recorded_hash, recorded_size), ("", ""))
                        continue
                    data = archive.read(name)
                    if recorded_hash:
                        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
                        self.assertEqual(recorded_hash, f"sha256={digest.decode()}")
                        self.assertEqual(recorded_size, str(len(data)))
                self.assertEqual(recorded_names, set(archive.namelist()))

    def test_rejects_bad_upstream_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "wrong.whl"
            source.write_bytes(b"not the verified pip wheel")
            with self.assertRaisesRegex(ValueError, "upstream pip wheel SHA256 mismatch"):
                rebuild_pip_seed_wheel.rebuild(source, root, root / "out.whl")


if __name__ == "__main__":
    unittest.main()
