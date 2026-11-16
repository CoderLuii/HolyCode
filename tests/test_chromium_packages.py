import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ChromiumPackagesTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.bash = "C:/Program Files/Git/bin/bash.exe" if os.name == "nt" else shutil.which("bash")
        if not self.bash:
            self.skipTest("Bash is required")
        scripts = {
            "docker": '''printf 'docker\\n' >> "$CALL_LOG"
while [ "$1" != --entrypoint ]; do shift; done
entrypoint="$2"; shift 2
shift
if [ "$entrypoint" = sh ]; then shift; exec bash -c "$1"; fi
exec "$entrypoint" "$@"
''',
            "apt-get": '''printf 'apt-get\\n' >> "$CALL_LOG"
exit "${FAIL_APT:-0}"
''',
            "dpkg-query": '''printf 'dpkg-query\\n' >> "$CALL_LOG"
[ "${MISSING_PACKAGE:-}" != "$3" ] || exit 1
printf '%s' "${INSTALLED:-156.0.8078.79-1~deb13u1}"
''',
            "apt-cache": '''printf 'apt-cache\\n' >> "$CALL_LOG"
printf 'Candidate: %s\\n' "${AVAILABLE:-156.0.8078.79-1~deb13u1}"
''',
            "dpkg": '''if [ "$1" = --print-architecture ]; then printf '%s\\n' "${ARCH:-amd64}"; exit; fi
[ "$1" = --compare-versions ] && [ "$3" = ge ] || exit 2
[ "$2" = '156.0.8078.79-1~deb13u1' ] && [ "$4" = '156.0.8078.79-1~deb13u1' ]
''',
            "validate-holycode-chromium-version": '''printf 'floor\\n' >> "$CALL_LOG"
exec bash "$FLOOR_SCRIPT" "$@"
''',
        }
        for name, body in scripts.items():
            file = self.root / name
            file.write_text("#!/usr/bin/env bash\nset -eu\n" + body, encoding="utf-8", newline="\n")
            file.chmod(0o755)

    def run_check(self, extra=None, script=None):
        log = self.root / "calls.log"
        log.write_text("", encoding="utf-8")
        env = {**os.environ, "CALL_LOG": log.as_posix(), "FIXTURE_TOOLS": self.root.as_posix(),
               "FLOOR_SCRIPT": (ROOT / "scripts/validate_chromium_version.sh").as_posix(),
               **(extra or {})}
        prefix = 'export PATH="$(cygpath -u "$FIXTURE_TOOLS"):$PATH";\n' if os.name == "nt" else 'export PATH="$FIXTURE_TOOLS:$PATH";\n'
        code = script or 'bash scripts/check_chromium_packages.sh fixture:latest linux/amd64 v1.3.0'
        result = subprocess.run([self.bash, "--noprofile", "--norc", "-c", prefix + code],
                                cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
        return result, log.read_text(encoding="utf-8").splitlines()

    def test_one_refresh_checks_all_three_packages(self):
        result, calls = self.run_check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls.count("docker"), 1)
        self.assertEqual(calls.count("apt-get"), 1)
        self.assertEqual(calls.count("dpkg-query"), 3)
        self.assertEqual(calls.count("floor"), 3)
        self.assertEqual(len(result.stdout.splitlines()), 3)

    def test_repository_failure_wrong_architecture_and_missing_package_block(self):
        for extra in ({"FAIL_APT": "1"}, {"ARCH": "arm64"}, {"MISSING_PACKAGE": "chromium-common"}):
            with self.subTest(extra=extra):
                result, _ = self.run_check(extra)
                self.assertNotEqual(result.returncode, 0)

    def test_outdated_installation_and_invalid_candidate_block(self):
        for extra in ({"INSTALLED": "155.0.0"}, {"AVAILABLE": "157.0.0"}, {"AVAILABLE": "(none)"}):
            with self.subTest(extra=extra):
                result, _ = self.run_check(extra)
                self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
