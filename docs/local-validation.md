# Release and validation guide

Use one manual GitHub Actions workflow for native qualification and release delivery. Run local source checks before committing or pushing. Do not run a second pre-tag image build first. The optional **HolyCode - Source checks** workflow is for development, not a release prerequisite.

Both workflows are manual-only. Pushes, PRs, tags and published releases do not start them. No continuously running self-hosted runner is required. Native AMD64 and ARM64 remain mandatory; emulation does not qualify a release. All browser checks use isolated headless contexts, controlled viewports and saved artifacts. Never open reports or personal browser sessions automatically.

## Before committing or pushing

Work from a clean isolated checkout of current `main`. Preserve unrelated worktrees, edits and persistent data. Match existing patterns and keep changes coherent. Use the pinned Node version from the workflow and Linux tools for Linux-specific checks:

```bash
python -m unittest discover -s tests
python scripts/validate_workflow_pins.py
python scripts/validate_chromium_seccomp.py
python -m json.tool renovate.json >/dev/null
python -m json.tool config/npm-global-script-policy.json >/dev/null
ruby -e 'require "yaml"; Dir[".github/workflows/*.{yml,yaml}"].each { |path| YAML.load_file(path) }'
docker compose -f docker-compose.yaml config --no-interpolate >/dev/null
docker compose -f docker-compose.full.yaml config --no-interpolate >/dev/null
bash scripts/validate_renovate_extraction.sh 44.129.0
```

A Windows pass with a skipped Linux check is partial evidence. Record the gap. Native qualification runs once in the manual workflow; source tests alone do not qualify images.

## Validate without publishing a release

After an authorized push makes the exact source available on `main`:

```bash
gh workflow run docker-publish.yml --ref main -f mode=validate
```

`validate` is the default. It accepts non-release commit subjects, runs the full native/runtime/scanner pipeline and publishes run-scoped candidate tags to GHCR. It does not promote version or `latest` aliases, upload release assets, publish a GitHub release or update the Docker Hub description. No draft is required. This still consumes hosted minutes and registry storage; dispatch deliberately.

## Prepare and deliver a release

1. Select the next single-digit version, such as `v1.3.1` after `v1.3.0`.
2. Update `ARG RELEASE_VERSION` in `Dockerfile` and the matching workflow `RELEASE_VERSION`. Update workflow `PREVIOUS_VERSION` and `PREVIOUS_IMAGE` to the actual published predecessor and its verified immutable digest. The pin validator checks agreement. Do not edit historical audits to make a new release pass.
3. Update the changelog, dependency audit, affected public docs and runtime fixtures. Keep accepted upstream findings explicit; acceptance is not a fix or safety claim.
4. Finish local checks, commit the coherent release change directly on `main` with subject `vX.Y.Z`, and push only when authorized. Other reviewed main commits may exist since the previous release. The workflow checks ancestry and exact source, not an arbitrary commit count. Do not invent a release PR to work around rules.
5. Create a source-bound draft with matching version/tag/title and a body starting `## MM/DD/YYYY`. Never reuse public versions or immutable assets. Draft-reading jobs require `contents: write`; read-only tokens cannot see drafts.
6. Dispatch once:

```bash
gh workflow run docker-publish.yml --ref main -f mode=release
```

There is no separately typed version input to disagree with source. The current main tip and commit subject must match the release source. The owner-authorized direct-main path remains policy; retain the Actions-owned `release-validation` context. If repository rules prevent that path, report the conflict instead of changing rules or opening a PR silently.

## What runs once

| Stage | Required result |
| --- | --- |
| validate-source | Exact source/main/ancestry and versions; publication-only draft/alias guard; credentials; full source/static suite |
| build-candidate | Parallel native AMD64/ARM64 builds, immutable digests, SBOM and maximum BuildKit provenance |
| compose-candidate | Combine exact native manifests and bound attestations; reject missing, changed or duplicate descriptors |
| protected-validation | Pull combined digest on both native runners; smoke/sandbox, plugins, removed-Hermes refusal/data preservation, Chromium floor/current availability, upgrade/persistence/untouched-snapshot rollback, Trivy/Scout, secret policy, inventories and SPDX |
| release-validation | Every prerequisite succeeds; failures, cancellations and skips block promotion |
| promote-candidate | Release mode only: recheck draft/unused aliases, promote the qualified graph without rebuilding, verify registries and upload evidence without clobbering |
| update-dockerhub-description | Release mode only, after promotion; failure does not invalidate image qualification |

Chromium uses one disposable container and one repository refresh for all three packages. Every package still passes both security-floor and installed-versus-available checks. Keep scanner execution, malformed reports, project-owned findings and secrets blocking. Known third-party findings remain advisory under the evidence policy.

Native caches accelerate builds but never count as runtime, scan, rollback or source-identity evidence. Keep pinned scanner archives/actions, non-root operation, sandbox/seccomp and closed browser port. Do not custom-patch dependencies to force an update through.

## Failure and resume rules

- Save the first actionable error, run, SHA, image digest and stage. Classify product/test, dependency, tooling, transport, quota/billing and permission failures separately.
- Reproduce deterministic failures narrowly. Do not retry unchanged failures. Allow at most one bounded retry of clearly transient transport errors. After two unsuccessful corrections to the same problem, stop the release attempt and present the blocker.
- For an owner-graph version mismatch, first install the exact parent package in a disposable prefix under the pinned Node/npm versions. Verify the actual resolved graph, official tarball integrity and existing consumer checks before changing expectations. Registry metadata alone is not compatibility evidence. Current unreleased corrections are recorded in [the dependency audit](dependency-audit-unreleased.md).
- Changed source/image inputs require fresh affected qualification. Never reuse runtime/scanner results for another image.
- Report-transfer failures do not require rebuilding qualified images. Resume the affected stage only with matching inputs and retained prerequisite evidence. Missing evidence is not success.
- GitHub job reruns use the original SHA and rerun dependent jobs. Check publication state first. Partial promotion or asset upload needs reconciliation: the immutable-alias guard intentionally blocks ordinary retries once aliases exist. Never delete public aliases or add `--clobber` to bypass it.
- A description-only failure can rerun that job without rebuilding images. An unavailable runner or account quota is an infrastructure blocker, not permission to spend days creating a new controller.
- Record the cause and prevention check before retrying. Keep release concurrency enabled. Never prune shared Docker resources, stop unrelated containers or alter Docker/WSL limits. Workflow cleanup applies only to disposable hosted runners.

## Measure completed runs

```bash
python scripts/report_release_timings.py --run-id RUN_ID --output artifacts/release-timings.json
```

Repeat `--run-id` to collect samples. Keep each run's SHA, conclusion, total duration, jobs and steps. Compare validation with validation and release with release. Queue time, caches, source and upstream package availability affect timing. Failed/incomplete runs do not prove speedups. The timing reporter records rerun attempts but excludes them from benchmark medians because the total includes time between attempts. Record two successful runs of the same candidate before claiming a repeatable improvement. Historical calculations are not new native benchmarks.

Optimize the measured bottleneck one change at a time. Keep changes only when coverage stays intact and repeated timing improves. Stop when improvements fall within normal variation, weaken checks or require disproportionate complexity. Every future release cannot be guaranteed faster than its predecessor.

## Finish publication; synchronize the site separately

Verify version tags, registry graphs, attestations, release assets and checksums before publishing the completed draft. Image signing is not configured; do not claim signatures. Preserve immutable releases and use the next version for later fixes.

After publication, synchronize site facts, qualify one site build locally/headlessly, deploy those exact bytes and verify immutable and canonical HTTPS URLs. Site or description failures must not restart product builds or releases.

## Explicit local fallback

Use local native delivery only when explicitly selected and both native hosts are ready before starting. The older `report_local_status.py` and its `local/source-validation`, `local/native-amd64`, `local/native-arm64` and post-publication `local/release-integrity` contexts remain supported. They validate registered plans and receipts; they do not run tests. Preserve trusted controller/source/tool/digest binding and pending/error semantics. Do not impersonate Actions-owned checks or substitute local statuses for the hosted aggregate.

Historical dependency audits describe their original release routes. This guide defines the current route. Do not rebuild a private orchestration system as an unplanned fallback during delivery.
