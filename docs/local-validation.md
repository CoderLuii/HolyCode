# Local validation and release results

Run normal qualification on maintainer-controlled infrastructure. GitHub stores the release and displays the results. You can explicitly authorize the manual hosted release route described below. No unattended self-hosted runner is installed.

Use native AMD64 and native ARM64 hosts. Keep the same source, runtime, sandbox, plugin, upgrade/persistence/rollback, scanner, secret, inventory, SPDX and provenance gates. Emulation does not replace a native architecture check. All browser automation uses isolated headless contexts and controlled viewports.

## Before running checks

Review the exact source, select the locked tools and register the command plan with the trusted local controller. Keep state, evidence and credentials outside the checkout and test containers. Do not run unreviewed pull-request code with status or release credentials.

Freeze the tracked source as a canonical descriptor containing the repository, commit, tree and every path's mode, Git blob ID, size and SHA256. Verify raw worktree bytes against the Git tree before and after the commands. Freeze the controller, its imports and tool inventory too. A changed source, command or tool invalidates the result.

The trusted host records actual command arguments, working directory, times, exit status, stdout/stderr hashes and required artifacts. A PASS field alone is insufficient. These hashes detect substitutions; they are not an independent execution attestation against a malicious maintainer host.

## Local status contexts

| Context | Required result |
| --- | --- |
| `local/source-validation` | Full Python suite, workflow/release and seccomp validation, JSON/YAML/Compose checks, external-only CLIProxyAPI check and Renovate extraction |
| `local/native-amd64` | Exact native image/build identity, first-party files, all pretag/protected checks, complete scanner evidence, inventories, SPDX and provenance |
| `local/native-arm64` | The same coverage on native ARM64 |
| `local/release-integrity` | Actual published release/tag/source, registry graphs, release asset bytes and applicable moving-alias readback |

The integrity context is post-publication. Do not require it before a merge or create a publication/merge dependency cycle. Local statuses do not impersonate existing Actions-owned checks. Review required-context/provider changes separately before changing repository rules.

The hosted release route uses the Actions-owned `release-validation` aggregate. Require that check for hosted delivery; do not substitute successful `local/*` statuses for its actual jobs or post local success from hosted results. A new release commit or newly built image needs evidence for that exact source and candidate digest. Local results for an earlier commit or image remain historical.

`pending` means qualification or reporting is in progress. `success` requires every mandatory stage and evidence check to pass. Test failures report `failure`; unavailable tools, interrupted execution, bad evidence and uncertain outcomes report `error`. Older attempts cannot overwrite a newer run's result.

## Reporter commands

For local qualification, the reporter validates the trusted controller's registered plan and receipts, then reports them for the exact commit. It does not execute tests. Use the same repository, commit, context and unique run ID for all three commands:

```bash
python scripts/report_local_status.py begin \
  --state-dir "$STATE_DIR" --repo CoderLuii/HolyCode --sha "$SHA" \
  --run-id "$RUN_ID" --context local/source-validation --plan source-plan.json

# Execute the registered source checks through the trusted local controller.

python scripts/report_local_status.py finish \
  --state-dir "$STATE_DIR" --repo CoderLuii/HolyCode --sha "$SHA" \
  --run-id "$RUN_ID" --context local/source-validation --evidence source-evidence.json

python scripts/report_local_status.py sync \
  --state-dir "$STATE_DIR" --repo CoderLuii/HolyCode --sha "$SHA" \
  --run-id "$RUN_ID" --context local/source-validation
```

An unpublished commit gets a local pending record first. Finish its local qualification before pushing. Once the approved push makes that exact SHA available on GitHub, `sync` publishes pending and the verified terminal result. Do not push an unqualified branch just to enable reporting.

When retesting an already-published SHA, add `--published` to `begin` so GitHub receives pending before tests start. A denied pending write does not authorize a successful terminal result. Do not bypass the shared state directory or reuse run IDs.

Authenticate through the trusted host's `gh` session. The reporter captures credentials in memory and does not pass them to tests. Fine-grained tokens need commit-status write permission; classic tokens need `repo:status` or `repo`. Report an access failure instead of probing with a fabricated success or adding scopes silently. Private paths and raw credential-bearing errors never belong in status descriptions or public evidence.

## Publish a locally qualified release

When you use the local route, qualify the exact committed source and both native images before pushing through the established direct-main path. Publish the sealed image graph once and verify all remote bytes locally. Prepare the complete assets and sanitized qualification summary in a draft release, verify them, then publish the draft last.

Post `local/release-integrity` success only after actual published readback. Verify historical version tags independently of moving `main` and `latest`; check moving aliases only while the release remains designated current, with a final identity recheck. Never overwrite a published version or immutable release asset to retry a check.

Synchronize the separate website after product publication. Build, test, audit and capture locally, upload that same qualified build, and verify the immutable deployment and public domain from local headless contexts.

## Opt-in hosted release

Both workflow files remain manual-only. Their `confirm_hosted_execution` input defaults to false. Pushing a commit, opening a pull request, tagging or publishing a release does not start them. Use the hosted route only when you have separately authorized it for the exact release commit on `main`.

The publisher in `.github/workflows/docker-publish.yml` runs the following sequence:

1. `validate-source` checks the source-bound draft, verifies Docker Hub credentials before builds, and runs the source/static checks once.
2. `build-candidate` builds AMD64 on `ubuntu-24.04` and ARM64 on `ubuntu-24.04-arm` in parallel. Each native build publishes its own immutable candidate digest with SBOM and provenance attestations. QEMU is not used.
3. `compose-candidate` reads the two per-architecture digest artifacts from the same run, verifies their native platforms and attestation targets, and combines their exact descriptors. It rejects a combined index that drops or changes a native manifest or attestation.
4. `protected-validation` pulls that combined candidate by digest on both native runners. It runs the four protected runtime checks, including sandbox, offline plugins, Chromium availability and upgrade/persistence/rollback, and collects the complete scanner, secret, inventory and SPDX evidence once per architecture. It does not rebuild the candidate or repeat the separate pretag workflow.
5. `release-validation` succeeds only when source validation, both native builds, composition and the complete protected matrix succeed. A failed, cancelled or skipped prerequisite blocks promotion.
6. `promote-candidate` promotes the verified combined graph through the existing guarded release path.

For an explicitly authorized hosted release, dispatch the exact version from `main`:

```bash
gh workflow run docker-publish.yml --ref main \
  -f confirm_hosted_execution=true -f release_version=v1.3.0
```

The manual publisher requires an exact source-bound draft and absent version image aliases. It rechecks those preconditions immediately before promotion and uploads without clobbering existing release assets. A read-only precondition cannot lock out an unrelated concurrent publisher: keep operator exclusion and workflow concurrency in force. Publish the completed draft only after all checks and readbacks are verified.

Hosted builds create a fresh candidate from the dispatched commit. Passing local checks on an earlier source does not qualify that new candidate. Keep the local reporter states and the hosted Actions results separate. The manual PR-validation workflow remains available for a separately requested validation run; the publisher does not dispatch it.

The cancelled v1.2.9 Actions run remains an accurate historical record. New local statuses do not turn that old cancellation into a hosted success.
