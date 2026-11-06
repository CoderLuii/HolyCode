#!/usr/bin/env python3
import argparse
import hashlib
import http.client
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


SOURCE_STAGES = {
    "python-tests", "workflow-pins", "chromium-seccomp", "renovate-json",
    "npm-policy-json", "workflow-yaml", "compose-default", "compose-full",
    "external-cliproxy-absent", "renovate-extraction",
}
NATIVE_STAGES = {
    "native-build", "native-identity", "firstparty-copy",
    "smoke-test-image-tools-and-secret-hygiene",
    "validate-drizzle-esbuild-remediation", "validate-plugin-pin-modes",
    "validate-chromium-security-floor-and-refreshed-availability",
    "smoke-test-paperclip-skills-catalog", "smoke-test-paperclip-runtime-environment",
    "validate-hermes-migration-guard",
    "protected-smoke-test-tools-and-chromium-sandbox",
    "protected-validate-offline-plugin-modes",
    "protected-validate-chromium-security-floor-and-refreshed-availability",
    "protected-validate-upgrade-persistence-and-rollback",
    "spdx", "scout-full", "scout-fixable", "trivy-full", "trivy-fixable",
    "scout-policy", "trivy-policy", "provenance", "inventory",
}
NATIVE_ARTIFACTS = {
    "native-build": {"image-metadata"}, "native-identity": {"native-identity"},
    "firstparty-copy": {"firstparty"}, "trivy-full": {"trivy-full", "secrets"},
    **{stage: {stage} for stage in (
        "spdx", "scout-full", "scout-fixable", "trivy-fixable",
        "scout-policy", "trivy-policy", "provenance", "inventory",
    )},
}
NATIVE_ARTIFACTS = {
    stage: NATIVE_ARTIFACTS.get(stage, set()) | {"inner-command", "inner-spec"}
    for stage in NATIVE_STAGES
}
RELEASE_STAGES = {"release-identity", "registry-readback", "release-assets", "moving-aliases"}
CONTEXTS = {
    "local/source-validation": SOURCE_STAGES,
    "local/native-amd64": NATIVE_STAGES,
    "local/native-arm64": NATIVE_STAGES,
    "local/release-integrity": RELEASE_STAGES,
}
IDENTITY_FIELDS = ("repository", "sha", "run_id", "context")


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def decode(raw):
    value = json.loads(raw, object_pairs_hook=unique_object)
    if not isinstance(value, dict):
        raise ValueError("JSON document must be an object")
    return value


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def timestamp(value, allow_offset=False):
    require(isinstance(value, str), "UTC timestamp required")
    if allow_offset and value.endswith("+00:00"):
        value = value[:-6] + "Z"
    require(isinstance(value, str) and value.endswith("Z"), "UTC timestamp required")
    return datetime.fromisoformat(value[:-1] + "+00:00")


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def child_path(root, value):
    require(isinstance(value, str) and value and "\\" not in value and ":" not in value,
            "relative evidence path required")
    relative = PurePosixPath(value)
    require(not relative.is_absolute() and ".." not in relative.parts, "path escapes root")
    path = root.joinpath(*relative.parts)
    require(path.resolve().is_relative_to(root.resolve()), "path escapes root")
    current = path
    while True:
        require(not current.is_symlink() and not (hasattr(current, "is_junction") and current.is_junction()),
                "symbolic links and junctions are not evidence paths")
        if current.parent == current:
            break
        current = current.parent
    return path


def read_record(root, record):
    require(isinstance(record, dict), "file descriptor required")
    digest = record.get("sha256")
    require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest), "invalid digest")
    require(type(record.get("bytes")) is int and record["bytes"] >= 0, "invalid file size")
    path = child_path(root, record.get("path"))
    raw = path.read_bytes()
    require(len(raw) == record["bytes"] and sha256(raw) == digest, "file seal mismatch")
    return raw


def identity_matches(value, identity):
    require(value.get("schema") == 1, "unsupported evidence schema")
    for key in IDENTITY_FIELDS:
        require(value.get(key) == identity[key], "evidence identity mismatch")


def git(repo, *args):
    # Source inspection never inherits host status credentials or Git hooks/config.
    env = {key: os.environ[key] for key in ("PATH", "SystemRoot", "TEMP", "TMP") if key in os.environ}
    env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_NO_REPLACE_OBJECTS": "1"})
    result = subprocess.run(
        ["git", "--no-replace-objects", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=" + os.devnull,
         "-C", str(repo), *args], env=env, capture_output=True, timeout=60,
    )
    require(result.returncode == 0, "source Git inspection failed")
    return result.stdout


def verify_source(plan):
    root = Path(plan["evidence_root"])
    repo = Path(plan["repo_dir"])
    require(repo.is_absolute() and root.is_absolute(), "absolute trusted paths required")
    raw = read_record(root, plan["source_manifest"])
    require(sha256(raw) == plan["source_sha256"], "source descriptor digest mismatch")
    source = decode(raw)
    require(raw == canonical(source), "source descriptor must use canonical JSON")
    require(source.get("schema") == 1 and source.get("repository") == plan["repository"]
            and source.get("sha") == plan["sha"], "source identity mismatch")
    require(git(repo, "rev-parse", "HEAD").decode().strip() == plan["sha"], "wrong source HEAD")
    tree = git(repo, "rev-parse", "HEAD^{tree}").decode().strip()
    require(source.get("tree") == tree, "source tree mismatch")
    entries = []
    index_entries = []
    for item in git(repo, "ls-tree", "-rz", "--full-tree", plan["sha"]).split(b"\0"):
        if not item:
            continue
        metadata, name = item.split(b"\t", 1)
        mode, kind, blob = metadata.decode().split()
        require(kind == "blob" and mode in {"100644", "100755"}, "unsupported source entry")
        path = name.decode("utf-8")
        file_path = child_path(repo, path)
        content = file_path.read_bytes()
        require(hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest() == blob,
                "source blob identity mismatch")
        require(content == git(repo, "cat-file", "blob", blob), "tracked source bytes changed")
        if os.name != "nt":
            require(bool(file_path.stat().st_mode & 0o111) == (mode == "100755"), "source mode changed")
        entries.append({"path": path, "mode": mode, "blob_sha1": blob,
                        "bytes": len(content), "sha256": sha256(content)})
        index_entries.append(f"{mode} {blob} 0\t{path}".encode("utf-8"))
    require(source.get("files") == sorted(entries, key=lambda item: item["path"]), "source file manifest mismatch")
    actual_index = git(repo, "ls-files", "--stage", "-z").split(b"\0")
    require(sorted(item for item in actual_index if item) == sorted(index_entries), "source index changed")


def dockerfile_copy_mappings(raw, source_files):
    mappings = set()
    destinations = set()
    from_count = 0
    for line in raw.decode("utf-8").splitlines():
        instruction = re.match(r"^\s*(FROM|COPY|ADD)\b", line, re.IGNORECASE)
        if not instruction:
            continue
        kind = instruction[1].upper()
        if kind == "FROM":
            from_count += 1
            continue
        require(kind == "COPY" and not line.rstrip().endswith("\\"), "unsupported Dockerfile copy form")
        tokens = shlex.split(line)[1:]
        while tokens and tokens[0].startswith("--"):
            require(re.fullmatch(r"--chmod=[0-7]{3,4}", tokens[0]), "unsupported Dockerfile COPY flag")
            tokens.pop(0)
        require(len(tokens) == 2, "single-file plain Dockerfile COPY required")
        source, destination = tokens
        require(source in source_files and not any(char in source + destination for char in "*?[]$\\")
                and not PurePosixPath(source).is_absolute() and ".." not in PurePosixPath(source).parts
                and PurePosixPath(destination).is_absolute() and ".." not in PurePosixPath(destination).parts
                and not destination.endswith("/"), "unsupported Dockerfile COPY path")
        if destination.startswith("/tmp/"):
            continue
        require(destination not in destinations, "duplicate retained Dockerfile COPY destination")
        destinations.add(destination)
        mappings.add((source, destination))
    require(from_count == 1 and mappings, "single-stage Dockerfile retained COPY mappings required")
    return mappings


def validate_native_mappings(plan):
    source = decode(read_record(Path(plan["evidence_root"]), plan["source_manifest"]))
    source_files = {item["path"]: item for item in source["files"]}
    dockerfile = source_files.get("Dockerfile")
    require(isinstance(dockerfile, dict), "committed Dockerfile source descriptor required")
    raw = git(Path(plan["repo_dir"]), "show", plan["sha"] + ":Dockerfile")
    require(sha256(raw) == dockerfile.get("sha256") and len(raw) == dockerfile.get("bytes")
            and hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == dockerfile.get("blob_sha1"),
            "committed Dockerfile source mismatch")
    expected = dockerfile_copy_mappings(raw, source_files)
    mappings = plan.get("native_firstparty_files")
    require(isinstance(mappings, list) and mappings, "registered first-party copy mappings required")
    actual = set()
    for mapping in mappings:
        require(isinstance(mapping, dict) and isinstance(mapping.get("source"), str)
                and isinstance(mapping.get("destination"), str), "invalid copy mapping")
        pair = (mapping["source"], mapping["destination"])
        require(pair not in actual, "duplicate copy mapping")
        actual.add(pair)
    require(actual == expected, "registered copies differ from complete retained Dockerfile mappings")
    return expected


def validate_plan(plan, identity):
    identity_matches(plan, identity)
    require(isinstance(plan.get("tools"), list) and plan["tools"], "sealed controller and tool inventory required")
    for tool in plan["tools"]:
        read_record(Path(plan["evidence_root"]), tool)
    require(isinstance(plan.get("stages"), list), "command plan required")
    stages = {}
    for stage in plan["stages"]:
        require(isinstance(stage, dict), "invalid stage")
        stage_id = stage.get("id")
        require(isinstance(stage_id, str) and stage_id not in stages, "duplicate stage")
        argv = stage.get("argv")
        require(isinstance(argv, list) and argv and all(isinstance(arg, str) and arg for arg in argv),
                "exact command argv required")
        require(isinstance(stage.get("cwd"), str) and stage["cwd"], "exact command cwd required")
        roles = stage.get("required_artifacts")
        require(isinstance(roles, list) and all(isinstance(role, str) and role for role in roles)
                and len(set(roles)) == len(roles), "invalid artifact roles")
        required = (NATIVE_ARTIFACTS.get(stage_id, set()) if identity["context"].startswith("local/native-")
                    else {stage_id} if identity["context"] == "local/release-integrity" else set())
        require(required.issubset(roles), "required artifact role missing")
        if identity["context"].startswith("local/native-") or {"inner-command", "inner-spec"} & set(roles) or any(
                key in stage for key in ("inner_argv", "inner_cwd", "inner_wrapper_sha256")):
            require({"inner-command", "inner-spec"}.issubset(roles), "inner command artifacts required")
            inner_argv = stage.get("inner_argv")
            require(isinstance(inner_argv, list) and inner_argv
                    and all(isinstance(arg, str) and arg for arg in inner_argv), "registered inner argv required")
            require(isinstance(stage.get("inner_cwd"), str) and stage["inner_cwd"], "registered inner cwd required")
            require(isinstance(stage.get("inner_wrapper_sha256"), str)
                    and stage["inner_wrapper_sha256"] in {tool["sha256"] for tool in plan["tools"]},
                    "registered inner wrapper must be a sealed tool")
        stages[stage_id] = stage
    require(CONTEXTS[identity["context"]].issubset(stages), "required stage missing")
    if identity["context"].startswith("local/native-"):
        validate_native_mappings(plan)
    if identity["context"] == "local/release-integrity":
        release = plan.get("release")
        require(isinstance(release, dict) and type(release.get("id")) is int and release["id"] > 0
                and release.get("sha") == plan["sha"] and isinstance(release.get("tag"), str)
                and re.fullmatch(r"v[0-9]\.[0-9]\.[0-9]", release["tag"])
                and isinstance(release.get("candidate_digest"), str)
                and re.fullmatch(r"sha256:[0-9a-f]{64}", release["candidate_digest"]),
                "exact release subject required")
    verify_source(plan)
    return stages


def validate_native_artifacts(plan, artifacts):
    identity = artifacts["native-identity"]
    platform = "linux/" + plan["context"].removeprefix("local/native-")
    require(identity.get("source_sha") == plan["sha"] and identity.get("platform") == platform,
            "native source or platform mismatch")
    for key in ("candidate_digest", "native_index_digest", "manifest_digest", "config_digest"):
        require(isinstance(identity.get(key), str) and re.fullmatch(r"sha256:[0-9a-f]{64}", identity[key]),
                "invalid native digest")
    require(identity.get("engine_image_id") == identity["native_index_digest"]
            and identity.get("engine_platform_id") == identity["manifest_digest"], "native engine identity mismatch")
    diff_ids = identity.get("diff_ids")
    require(isinstance(diff_ids, list) and diff_ids and all(
        isinstance(digest, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", digest) for digest in diff_ids),
        "native rootfs digests required")
    provenance = artifacts["provenance"]
    require(provenance.get("source_sha") == plan["sha"]
            and provenance.get("candidate_digest") == identity["candidate_digest"], "provenance identity mismatch")
    platforms = provenance.get("platforms")
    require(isinstance(platforms, list) and all(isinstance(item, dict) for item in platforms),
            "provenance platform records required")
    selected = [item for item in platforms if item.get("platform") == platform]
    require(len(selected) == 1, "provenance selected platform missing or duplicated")
    record = selected[0]
    require(record.get("manifest_digest") == identity["manifest_digest"]
            and record.get("config_digest") == identity["config_digest"]
            and record.get("rootfs_diff_ids") == diff_ids, "provenance graph mismatch")
    require(isinstance(record.get("attestation_digest"), str)
            and re.fullmatch(r"sha256:[0-9a-f]{64}", record["attestation_digest"])
            and type(record.get("package_count")) is int and record["package_count"] > 0
            and record.get("provenance_origin") == "local BuildKit", "native attestation or inventory missing")
    firstparty = artifacts["firstparty"]
    for key in ("source_sha", "platform", "candidate_digest", "native_index_digest",
                "engine_image_id", "engine_platform_id", "manifest_digest", "config_digest"):
        require(firstparty.get(key) == identity[key], "first-party image identity mismatch")
    source = decode(read_record(Path(plan["evidence_root"]), plan["source_manifest"]))
    source_files = {item["path"]: item for item in source["files"]}
    files = firstparty.get("files")
    require(isinstance(files, list) and files, "first-party file observations missing")
    expected = validate_native_mappings(plan)
    seen = set()
    for item in files:
        require(isinstance(item, dict), "invalid first-party file observation")
        mapping = (item.get("source"), item.get("destination"))
        require(mapping in expected and mapping not in seen, "unexpected first-party copy mapping")
        source_file = source_files.get(item["source"])
        require(source_file is not None and item.get("size") == source_file["bytes"]
                and item.get("actual_size") == source_file["bytes"]
                and item.get("sha256") == source_file["sha256"]
                and item.get("actual_sha256") == source_file["sha256"], "first-party copied bytes differ from source")
        seen.add(mapping)
    require(seen == expected, "first-party copied file coverage incomplete")


def validate_release_artifacts(plan, artifacts, started_at):
    release = plan["release"]
    for role in RELEASE_STAGES:
        artifact = artifacts[role]
        require(artifact.get("release_id") == release["id"] and artifact.get("release_tag") == release["tag"]
                and artifact.get("source_sha") == release["sha"]
                and artifact.get("candidate_digest") == release["candidate_digest"], "release artifact subject mismatch")
        reports = artifact.get("reports")
        require(isinstance(reports, list) and reports, "sealed raw release readbacks required")
        for report in reports:
            read_record(Path(plan["evidence_root"]), report)
    identity = artifacts["release-identity"]
    require(identity.get("draft") is False and identity.get("tag_sha") == plan["sha"]
            and timestamp(identity.get("published_at")) <= timestamp(started_at),
            "release verification must follow publication of the exact tag")


def validate_inner_command(plan, outer, inner, spec_record):
    require(isinstance(inner, dict), "actual inner command receipt required")
    specification = decode(read_record(Path(plan["evidence_root"]), spec_record))
    require(inner.get("spec_sha256") == spec_record["sha256"], "inner command specification seal mismatch")
    for key in ("stage", "sha", "run_id", "context", "source_sha256", "plan_sha256"):
        require(inner.get(key) == outer[key] and specification.get(key) == outer[key], "inner command identity mismatch")
    stages = [stage for stage in plan["stages"] if stage.get("id") == outer["stage"]]
    require(len(stages) == 1, "registered inner command stage required")
    stage = stages[0]
    for key in ("argv", "cwd", "wrapper_sha256"):
        require(inner.get(key) == stage["inner_" + key] and specification.get(key) == stage["inner_" + key],
                "inner command differs from registered plan")
    for key in ("shared_job_id", "shared_owner"):
        require(inner.get(key) == specification.get(key), "inner command differs from specification")
        require(inner.get(key) == outer.get(key), "inner command differs from admitted job identity")
    require(isinstance(inner.get("argv"), list) and inner["argv"]
            and all(isinstance(arg, str) and arg for arg in inner["argv"])
            and isinstance(inner.get("cwd"), str) and inner["cwd"], "actual inner command required")
    require(inner.get("wrapper_sha256") in {tool["sha256"] for tool in plan["tools"]}, "unregistered stage wrapper")
    job_id = inner.get("shared_job_id")
    require(isinstance(job_id, str) and re.fullmatch(r"[0-9a-f]{16}", job_id)
            and inner.get("shared_owner") == "hf-holycode-" + job_id, "invalid admitted job ownership")
    start = timestamp(inner.get("started_at"), allow_offset=True)
    end = timestamp(inner.get("finished_at"), allow_offset=True)
    require(timestamp(outer["started_at"]) <= start <= end <= timestamp(outer["finished_at"]),
            "inner command timestamp outside wrapper interval")
    require(type(inner.get("exit_code")) is int and inner["exit_code"] == outer["exit_code"],
            "inner command exit differs from wrapper")
    for stream in ("stdout", "stderr"):
        require(isinstance(inner.get(stream), dict)
                and inner[stream].get("sha256") == outer[stream]["sha256"]
                and inner[stream].get("bytes") == outer[stream]["bytes"], "inner and outer streams differ")


def validate_evidence(state, raw):
    plan = state["plan"]
    stages = validate_plan(plan, state)
    evidence = decode(raw)
    identity_matches(evidence, state)
    require(evidence.get("plan_sha256") == state["plan_sha256"], "registered plan digest mismatch")
    require(evidence.get("source_sha256") == plan["source_sha256"], "source binding mismatch")
    outcome = evidence.get("outcome")
    require(outcome in {"completed", "failed", "error", "interrupted"}, "unknown execution outcome")
    start, end = timestamp(evidence.get("started_at")), timestamp(evidence.get("finished_at"))
    require(timestamp(state["began_at"]) <= start <= end <= datetime.now(timezone.utc),
            "execution timestamp outside registered attempt")
    root = Path(plan["evidence_root"])
    for key in ("source_before", "source_after"):
        source = read_record(root, evidence.get(key))
        require(sha256(source) == plan["source_sha256"], "source changed during execution")
    receipts = evidence.get("receipts")
    require(isinstance(receipts, list), "command receipts required")
    seen = set()
    failed = False
    native_artifacts = {}
    release_artifacts = {}
    for record in receipts:
        receipt = decode(read_record(root, record))
        identity_matches(receipt, state)
        require(receipt.get("plan_sha256") == state["plan_sha256"]
                and receipt.get("source_sha256") == plan["source_sha256"], "receipt binding mismatch")
        stage_id = receipt.get("stage")
        require(stage_id in stages and stage_id not in seen, "unknown or duplicate command receipt")
        stage = stages[stage_id]
        require(receipt.get("argv") == stage["argv"] and receipt.get("cwd") == stage["cwd"],
                "command differs from registered plan")
        require(start <= timestamp(receipt.get("started_at")) <= timestamp(receipt.get("finished_at")) <= end,
                "command timestamp outside context interval")
        code = receipt.get("exit_code")
        require(type(code) is int and code >= 0, "unknown or interrupted command exit")
        read_record(root, receipt.get("stdout"))
        read_record(root, receipt.get("stderr"))
        artifacts = receipt.get("artifacts")
        require(isinstance(artifacts, list), "artifact records required")
        roles = set()
        inner_command = None
        inner_spec = None
        for artifact in artifacts:
            require(isinstance(artifact, dict) and isinstance(artifact.get("role"), str)
                    and artifact["role"] not in roles, "invalid or duplicate artifact role")
            artifact_bytes = read_record(root, artifact)
            if plan["context"].startswith("local/native-") and artifact["role"] in {
                    "native-identity", "firstparty", "provenance"}:
                require(artifact["role"] not in native_artifacts, "duplicate native identity artifact")
                native_artifacts[artifact["role"]] = decode(artifact_bytes)
            if plan["context"] == "local/release-integrity" and artifact["role"] in RELEASE_STAGES:
                require(artifact["role"] not in release_artifacts, "duplicate release identity artifact")
                release_artifacts[artifact["role"]] = decode(artifact_bytes)
            if artifact["role"] == "inner-command":
                inner_command = decode(artifact_bytes)
            if artifact["role"] == "inner-spec":
                inner_spec = artifact
            roles.add(artifact["role"])
        if code == 0:
            require(set(stage["required_artifacts"]).issubset(roles), "required artifact missing")
            if "inner-command" in stage["required_artifacts"]:
                validate_inner_command(plan, receipt, inner_command, inner_spec)
        failed |= code != 0
        seen.add(stage_id)
    if outcome in {"error", "interrupted"}:
        return "error"
    if failed:
        return "failure"
    require(outcome == "completed" and seen == set(stages), "incomplete execution")
    if plan["context"].startswith("local/native-"):
        validate_native_artifacts(plan, native_artifacts)
    if plan["context"] == "local/release-integrity":
        validate_release_artifacts(plan, release_artifacts, evidence["started_at"])
    return "success"


@contextmanager
def state_lock(directory):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "reporter.lock").open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise ValueError("another local reporter owns the state lock") from None
        try:
            yield
        finally:
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def save_state(path, state):
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix="reporter-", suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(canonical(state))
            handle.flush()
            os.fsync(handle.fileno())
        except OSError:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def github_request(method, path, payload=None):
    require(method in {"GET", "POST"} and path.startswith("/repos/"), "invalid GitHub request")
    executable = shutil.which("gh")
    require(executable is not None, "GitHub CLI unavailable")
    auth = subprocess.run([executable, "auth", "token", "--hostname", "github.com"],
                          capture_output=True, timeout=30)
    require(auth.returncode == 0 and auth.stdout.strip(), "GitHub authentication unavailable")
    token = auth.stdout.strip().decode("utf-8")
    connection = http.client.HTTPSConnection("api.github.com", timeout=30)
    try:
        connection.request(method, path, body=canonical(payload) if payload is not None else None,
                           headers={"Authorization": "Bearer " + token,
                                    "Accept": "application/vnd.github+json",
                                    "X-GitHub-Api-Version": "2026-03-10",
                                    "User-Agent": "holycode-local-status",
                                    "Content-Type": "application/json"})
        response = connection.getresponse()
        require(response.status in {200, 201}, f"GitHub API rejected request (HTTP {response.status})")
        return decode(response.read()), dict(response.getheaders())
    except (OSError, http.client.HTTPException):
        raise ValueError("GitHub API transport unavailable") from None
    finally:
        connection.close()


def sync_state(path, state, transport):
    # Persist the remote boundary before a request can succeed without an acknowledgement.
    state["remote_known"] = True
    state["synced"] = False
    save_state(path, state)
    base = f"/repos/{state['repository']}"
    commit, headers = transport("GET", base + "/commits/" + state["sha"])
    require(commit.get("sha") == state["sha"], "remote commit identity mismatch")
    scopes = next((value for key, value in headers.items() if key.lower() == "x-oauth-scopes"), None)
    if scopes:
        require(bool({"repo", "repo:status"} & {scope.strip() for scope in scopes.split(",")}),
                "token metadata lacks commit status write scope")
    endpoint = base + "/statuses/" + state["sha"]
    for status in (["pending"] if not state.get("remote_started") else []) + (
            [state["state"]] if state["state"] != "pending" else []):
        description = f"Local validation {status}; run {state['run_id']}"
        payload = {"state": status, "context": state["context"], "description": description[:140]}
        result, _ = transport("POST", endpoint, payload)
        require(result.get("state") == status and result.get("context") == state["context"],
                "GitHub status acknowledgement mismatch")
        if status == "pending":
            state["remote_started"] = True
        state["remote_state"] = status
        save_state(path, state)
    state["synced"] = True
    save_state(path, state)


def run(action, state_dir, repository, sha, run_id, context, plan_file=None,
        evidence_file=None, published=False, transport=None):
    require(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository), "invalid repository")
    require(re.fullmatch(r"[0-9a-f]{40}", sha), "full commit SHA required")
    require(re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", run_id), "invalid run ID")
    require(context in CONTEXTS, "unsupported local status context")
    require(action in {"begin", "finish", "sync"}, "unknown reporter action")
    identity = dict(repository=repository, sha=sha, run_id=run_id, context=context)
    directory = Path(state_dir).resolve()
    with state_lock(directory):
        key = sha256(canonical([repository.lower(), sha, context]))
        path = directory / (key + ".json")
        state = decode(path.read_bytes()) if path.exists() else None
        if action == "begin":
            require(plan_file is not None, "begin requires a command plan")
            used_runs = state.get("used_runs", []) if state else []
            require(run_id not in used_runs, "run ID was already used")
            raw = Path(plan_file).read_bytes()
            plan = decode(raw)
            validate_plan(plan, identity)
            published = published or bool(state and (state.get("remote_known") or state.get("remote_started")
                                                     or state.get("remote_state")))
            state = dict(identity, schema=1, state="pending", synced=False,
                         plan=plan, plan_sha256=sha256(raw), began_at=now(),
                         attempt=(state["attempt"] + 1 if state else 1),
                         used_runs=used_runs + [run_id], remote_started=False, remote_known=published)
            save_state(path, state)
            if published:
                try:
                    sync_state(path, state, transport or github_request)
                except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError):
                    state["state"] = "error"
                    state["synced"] = False
                    save_state(path, state)
                    raise
        else:
            require(state is not None, "no registered local attempt")
            identity_matches(state, identity)
            if action == "finish":
                require(state["state"] == "pending", "terminal result requires a new attempt")
                require(evidence_file is not None, "finish requires evidence")
                try:
                    require(not state.get("remote_known") or state.get("remote_started"),
                            "published attempt requires acknowledged pending before execution")
                    evidence_path = Path(evidence_file).resolve()
                    require(evidence_path.is_relative_to(Path(state["plan"]["evidence_root"]).resolve()),
                            "evidence is outside registered root")
                    raw = evidence_path.read_bytes()
                    state["evidence"] = {"path": str(evidence_path), "sha256": sha256(raw)}
                    state["state"] = validate_evidence(state, raw)
                except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError):
                    state["state"] = "error"
                state["synced"] = False
                save_state(path, state)
            if action == "sync":
                if state["state"] != "pending":
                    try:
                        raw = Path(state["evidence"]["path"]).read_bytes()
                        require(sha256(raw) == state["evidence"]["sha256"], "evidence seal changed")
                        require(validate_evidence(state, raw) == state["state"], "terminal evidence changed")
                    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError):
                        state["state"] = "error"
                state["synced"] = False
                save_state(path, state)
                sync_state(path, state, transport or github_request)
        return {key: state[key] for key in ("state", "run_id", "attempt", "synced")}


def main():
    parser = argparse.ArgumentParser(description="Report sealed local validation to an exact GitHub commit.")
    parser.add_argument("action", choices=("begin", "finish", "sync"))
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--repo", dest="repository", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--context", required=True, choices=CONTEXTS)
    parser.add_argument("--plan", dest="plan_file", type=Path)
    parser.add_argument("--evidence", dest="evidence_file", type=Path)
    parser.add_argument("--published", action="store_true")
    args = parser.parse_args()
    try:
        result = run(**vars(args))
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        # Never echo arbitrary API bodies, command output, or private evidence fields.
        print(f"Local status reporter could not complete ({type(error).__name__}).", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {"pending", "success"} else 1


if __name__ == "__main__":
    sys.exit(main())
