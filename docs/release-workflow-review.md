# Release workflow: causes, changes and measured times

Release qualification stays in GitHub Actions. Use the [release guide](local-validation.md) for the next version. One manual workflow builds and validates native AMD64 and ARM64 candidates; release mode promotes the verified images without rebuilding them. Validation mode cannot publish a product release.

## Why releases kept turning into long sessions

Several failures had different causes. Repeating the entire release did not fix those causes.

| What happened | Evidence | What changed |
| --- | --- | --- |
| A matching draft was rejected because the source job could not see drafts with its read-only token. This was CI authorization. | [Failed run 42236799617](https://github.com/CoderLuii/HolyCode/actions/runs/42236799617), `validate-source`: `exactly one bound draft release is required`; its workflow used `contents: read`. The corrected [v1.3.0 run](https://github.com/CoderLuii/HolyCode/actions/runs/42238536860) passed. | Trusted main's draft-reading job has `contents: write`. Validation mode needs no draft; release mode keeps the source-bound draft check. |
| Paperclip's declared dependency range resolved official Cursor SDK 1.4.0 while the image guard expected 1.3.1. This was dependency drift. | Both native builds in [run 43779499362](https://github.com/CoderLuii/HolyCode/actions/runs/43779499362) rejected the graph. | Verified the official SDK and actual consumers before updating the expectation, integrity and fixtures. [Compatibility record](dependency-audit-unreleased.md). No package patch or removed guard. |
| A pnpm update shipped a newer internal HTTP client while the smoke test still expected the older bundle. This was a test expectation mismatch. | [First v1.3.1 attempt 43825219105](https://github.com/CoderLuii/HolyCode/actions/runs/43825219105): both builds passed; both protected jobs stopped after pnpm 12.21.0. The official payload embeds Undici 7.30.2, not 6.29.1. | Bind pnpm version/integrity and its embedded manifest to a regression fixture; check the strict expectation and actual bundled HTTP consumer before retrying. Keep the official package unchanged. |
| The development workflow built and scanned images, then release qualification built and checked them again. | [Previous development workflow](https://github.com/CoderLuii/HolyCode/blob/30f91535e0c28edc66c148341dbe721ec9a63748/.github/workflows/pr-validation.yml). | Development checks are source-only and optional. Release qualification owns the native builds and runtime/security checks. |
| Both architectures restored the same daily Trivy cache path. ARM64 repeatedly restored analysis from the other architecture. | Before isolation, three ARM64 Trivy stages took 250s and 229s; AMD64 took 14s and 13s. After separate paths and a warm repeat, ARM64 took 15s. | Separate architecture cache versions, shared within each architecture. All scans, freshness checks, reports and gates remain. |
| Release instructions and workflow conditions added avoidable coordination: a separately typed version and an exactly-one-intervening-commit assumption. | [Workflow simplification](https://github.com/CoderLuii/HolyCode/commit/b047bf1fe382b9932aac0f54fbe1ed01b5beef3a). | Read the version from source. Validate exact main identity, predecessor ancestry and release metadata. Reviewed maintenance commits can exist between releases. |

The expensive behavior was treating each red result as a reason for another broad attempt: rebuilding unchanged inputs, mixing dependency repair with release orchestration, switching delivery routes mid-attempt, or continuing without a recorded cause and a bounded next step. These choices add investigation and repeated waiting. The current guide requires a recorded cause, a narrow reproduction and explicit resume rules before another attempt.

The run history does **not** measure total conversation time or token charges. It cannot independently prove a 24–36 hour total, assign a token cost to a particular failure, or establish every older failure's root cause. Generic exit codes remain unknown until their logs establish a cause. Runner availability, transport, quota and billing failures must be classified separately from code/test failures; these five successful native samples do not prove those infrastructure problems can never recur.

## Actual completed GitHub timings

These are validation runs, not full publication or website deployments. Initial waiting is creation to the first executed job. Execution is that first job through run completion, including later job queues, runner preparation, builds, tests, scans and artifact transfer. Parallel job durations are not added together.

| Source | Run | Initial wait | Execution | Total |
| --- | --- | --- | --- | --- |
| SDK correction `e0a835f` | [43802342043](https://github.com/CoderLuii/HolyCode/actions/runs/43802342043) | 0:04 | 20:47 | 20:51 |
| npm download cache `59018ef` | [43804687643](https://github.com/CoderLuii/HolyCode/actions/runs/43804687643) | 0:04 | 15:33 | 15:37 |
| Same source repeat | [43806275480](https://github.com/CoderLuii/HolyCode/actions/runs/43806275480) | 0:04 | 15:24 | 15:28 |
| Architecture scanner caches `2c57dc3` | [43807835944](https://github.com/CoderLuii/HolyCode/actions/runs/43807835944) | 0:03 | 16:47 | 16:50 |
| Same source, warm repeat | [43808692359](https://github.com/CoderLuii/HolyCode/actions/runs/43808692359) | 8:43 | 12:45 | 21:28 |

The last repeat was deliberately queued behind the preceding run. Its 21:28 total is real; 12:45 excludes only that initial waiting. The first isolated-cache run populated empty caches and had slower runner preparation. Its total was worse than the earlier 15-minute runs. Do not hide that result or advertise 12:45 as a guaranteed release time.

The final source passed twice. Each run passed all seven required jobs, including both native architectures; the two publication jobs correctly skipped. Full Trivy result coverage, inventories and non-image SPDX package identities were compared across the change. Comparisons exclude timestamps and expected image/source metadata differences. Accepted upstream findings remain visible; a green policy gate is not a zero-vulnerability claim.

The npm cache repeat reduced the source job from 78s to 52s with a confirmed hit. Other caches and runner load also changed, so the whole workflow gain cannot be attributed to npm. The final warm scanner stages took 15s on ARM64 and 14s on AMD64. The [machine-readable timings](release-workflow-timings.json) retain every job and step, exact SHA, attempt and conclusion.

Reproduce the report without starting another build:

```bash
python scripts/report_release_timings.py --run-id 43807835944 --run-id 43808692359 --output artifacts/release-timings.json
```

The reporter keeps total and execution medians separate. Mixed source/workflow identities have no aggregate median. Reruns are excluded from benchmark medians and have no execution interval because time between attempts would distort it. Skipped jobs have no measured duration, including when GitHub supplies inverted timestamps.

## How to avoid another retry loop

1. Run the local source checks in the release guide before pushing. A source pass does not qualify native images.
2. Dispatch the release workflow once. Use `validate` for maintenance qualification; use `release` only for an authorized new version with a matching draft. Running `validate` first is not a mandatory second build before `release`.
3. On failure, save the run URL, SHA, job, step, first actionable error and image digest. Classify the cause before editing. Never call downstream missing-image errors a second independent build defect.
4. Reproduce a deterministic failure narrowly. Do not rerun unchanged deterministic failures. Allow at most one retry for a proven transient transport failure. After two unsuccessful corrections to the same problem, report the blocker instead of continuing an open-ended attempt.
5. Keep source, tools and image identity fixed when resuming an affected reporting/transport stage. Image-affecting changes require fresh downstream qualification. Inspect partial publication before rerunning; never overwrite public versions or clobber assets.
6. Finish registry/release verification before site synchronization. A description or website failure must not restart qualified product builds.
7. For speed work, change one measured bottleneck at a time, retain failed/slower samples, and get two successful runs of the same candidate. Preserve reports and state what changed in cache warmth or runner conditions.

## Why optimization stops here

The current low-risk changes have native evidence. The remaining time includes image transfer, sandbox/plugin execution, persistence/rollback and disposable-runner preparation. In the final pair, AMD64 disk preparation varied from 229s to 149s. Removing cleanup without cold-build disk measurements risks replacing a delay with disk exhaustion. Combining build and protected jobs would change the read-only validation boundary. Skipping native ARM64, reducing scanners or testing only warm caches would reduce coverage.

Those are separate experiments requiring new evidence, not justified shortcuts for this release task. No claim of an absolute fastest workflow is possible, and a future release with changed dependencies or GitHub runner conditions may take longer. Revisit optimization when completed-run evidence identifies a safe worthwhile change; do not spend repeated hosted runs chasing seconds within normal variation.

The timing rows above are workflow qualification samples. Plan 1x uses this workflow for the v1.3.1 maintenance release; its source-bound native evidence and publication results belong to that release. No product release aliases or site deployment were published by the validation-only samples above.


## v1.3.1 delivery result

The [v1.3.1 release run](https://github.com/CoderLuii/HolyCode/actions/runs/43828503867) passed all nine jobs from `d1c5c780e2ae330f983d0188b9b5f857741e0286`: 17m05s total, 17m02s execution and 3s initial wait. It promoted the qualified graph without rebuilding; both registries' version/latest aliases and all 24 downloaded release assets were verified before publication. This release changed the base image and dependencies, so its cold scanner work is not comparable to the earlier unchanged-image 11m04s warm validation sample. One successful release is not a repeatable speed benchmark.

The first release attempt, [43825219105](https://github.com/CoderLuii/HolyCode/actions/runs/43825219105), failed in the protected smoke checks because an exact assertion still expected pnpm's previous embedded Undici. Official pnpm 12.21.0 contains Undici 7.30.2. The repair updates that strict expectation and adds an integrity/manifest fixture plus regression coverage that rejects both the obsolete and a wrong newer version. Official package payload and HTTP/offline consumers passed locally before fresh native qualification. No dependency patch, skipped check or unchanged retry was used. The failed timing sample remains in the JSON alongside the successful run.

Site synchronization followed product publication. A provider-added analytics script made the first site's HTML differ from the sealed build. That site-only problem was corrected at the Pages project setting and the same qualified site files redeployed; product images were not rebuilt. Keep reporting and site recovery separate from completed product qualification.
