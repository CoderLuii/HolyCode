#!/usr/bin/env python3
"""Read completed GitHub runs and save actual workflow, job and step timings."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import statistics
import subprocess


def elapsed(start: str, end: str) -> float:
    return (datetime.fromisoformat(end.replace("Z", "+00:00"))
            - datetime.fromisoformat(start.replace("Z", "+00:00"))).total_seconds()


def summarize(run: dict, jobs: list[dict]) -> dict:
    if not run.get("conclusion"):
        raise ValueError("wait for the run to complete before measuring it")
    return {
        "run_id": run["id"], "sha": run["head_sha"], "conclusion": run["conclusion"],
        "workflow_id": run.get("workflow_id"), "run_name": run.get("display_title"),
        "run_attempt": run.get("run_attempt", 1),
        "benchmark_eligible": run.get("run_attempt", 1) == 1 and run["conclusion"] == "success",
        "elapsed_seconds": elapsed(run["created_at"], run["updated_at"]),
        "jobs": [
            {"name": job["name"], "conclusion": job["conclusion"],
             "elapsed_seconds": elapsed(job["started_at"], job["completed_at"]),
             "steps": [{"name": step["name"], "conclusion": step.get("conclusion"),
                        "elapsed_seconds": elapsed(step["started_at"], step["completed_at"])}
                       for step in job["steps"] if step.get("started_at") and step.get("completed_at")]}
            for job in jobs if job.get("started_at") and job.get("completed_at")
        ],
    }


def api(path: str) -> dict:
    return json.loads(subprocess.check_output(["gh", "api", path], text=True, encoding="utf-8", timeout=60))


def read_run(repository: str, run_id: int) -> dict:
    prefix = f"repos/{repository}/actions/runs/{run_id}"
    run = api(prefix)
    jobs = []
    page = 1
    while True:
        batch = api(f"{prefix}/jobs?per_page=100&page={page}")["jobs"]
        jobs.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return summarize(run, jobs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default="CoderLuii/HolyCode")
    parser.add_argument("--run-id", type=int, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository):
        parser.error("repository must be owner/name")
    runs = [read_run(args.repository, run_id) for run_id in args.run_id]
    identities = {(run["workflow_id"], run["sha"], run["run_name"]) for run in runs}
    successful = [run["elapsed_seconds"] for run in runs if run["benchmark_eligible"]] if len(identities) == 1 else []
    report = {
        "repository": args.repository,
        "scope": "Actual completed run durations, including queue/setup. Different sources, caches and runner load can affect comparisons.",
        "runs": runs,
        "successful_median_seconds": statistics.median(successful) if successful else None,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "runs": len(runs),
                      "successful_median_seconds": report["successful_median_seconds"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
