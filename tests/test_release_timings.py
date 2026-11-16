import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReleaseTimingTests(unittest.TestCase):
    def test_measures_elapsed_and_steps_without_counting_parallel_jobs_twice(self):
        path = ROOT / "scripts/report_release_timings.py"
        self.assertTrue(path.is_file(), "release timing reporter is missing")
        spec = importlib.util.spec_from_file_location("release_timings", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        run = {"id": 1, "head_sha": "a" * 40, "conclusion": "success",
               "created_at": "2026-11-15T10:00:00Z", "updated_at": "2026-11-15T10:03:00Z"}
        jobs = [{"name": name, "conclusion": "success", "started_at": "2026-11-15T10:00:00Z",
                 "completed_at": "2026-11-15T10:02:00Z", "steps": []} for name in ("amd64", "arm64")]
        result = module.summarize(run, jobs)
        self.assertEqual(result["elapsed_seconds"], 180)
        self.assertEqual(result["initial_wait_seconds"], 0)
        self.assertEqual(result["execution_elapsed_seconds"], 180)
        self.assertEqual([j["elapsed_seconds"] for j in result["jobs"]], [120, 120])
        run["run_attempt"] = 2
        self.assertFalse(module.summarize(run, jobs)["benchmark_eligible"])
        self.assertIsNone(module.summarize(run, jobs)["execution_elapsed_seconds"])
        run["conclusion"] = None
        with self.assertRaises(ValueError):
            module.summarize(run, jobs)

    def test_separates_initial_wait_and_ignores_skipped_job_timestamps(self):
        spec = importlib.util.spec_from_file_location("release_timings", ROOT / "scripts/report_release_timings.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        run = {"id": 1, "head_sha": "a" * 40, "conclusion": "success",
               "created_at": "2026-11-15T10:00:00Z", "updated_at": "2026-11-15T10:10:00Z"}
        jobs = [{"name": "source", "conclusion": "success", "started_at": "2026-11-15T10:03:00Z",
                 "completed_at": "2026-11-15T10:04:00Z", "steps": []},
                {"name": "promotion", "conclusion": "skipped", "started_at": "2026-11-15T10:00:01Z",
                 "completed_at": "2026-11-15T10:00:00Z", "steps": []}]
        result = module.summarize(run, jobs)
        self.assertEqual(result["elapsed_seconds"], 600)
        self.assertEqual(result["initial_wait_seconds"], 180)
        self.assertEqual(result["execution_elapsed_seconds"], 420)
        self.assertIsNone(result["jobs"][1]["elapsed_seconds"])
        result = module.summarize(run, jobs[1:])
        self.assertIsNone(result["initial_wait_seconds"])
        self.assertIsNone(result["execution_elapsed_seconds"])


if __name__ == "__main__":
    unittest.main()
