#!/usr/bin/env python3
"""Refuse reuse of a HolyCode release target before building or promoting it.

Run again immediately before promotion with --require-draft and
--previous-digest (64 hex characters, without sha256:). GH_TOKEN is read only
from the environment. Only GitHub metadata and anonymous public registry
metadata are read. This check cannot lock out concurrent external publishers.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


REPOSITORY = "CoderLuii/HolyCode"
IMAGE = "coderluii/holycode"
OFFICIAL_HOSTS = {"api.github.com", "auth.docker.io", "registry-1.docker.io", "ghcr.io"}
ACCEPT_MANIFEST = ", ".join((
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
))
MAX_BODY = 2 * 1024 * 1024


class ReleaseTargetError(ValueError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True)
class Response:
    status: int
    headers: dict[str, str]
    body: bytes


class HttpClient:
    def __init__(self):
        self.opener = urllib.request.build_opener(
            NoRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context())
        )

    def get(self, url: str, headers: dict[str, str] | None = None) -> Response:
        parsed = urllib.parse.urlsplit(url)
        if (parsed.scheme != "https" or parsed.hostname not in OFFICIAL_HOSTS
                or parsed.username is not None or parsed.password is not None
                or parsed.port not in (None, 443) or parsed.fragment):
            raise ReleaseTargetError("only official HTTPS metadata endpoints are allowed")
        request = urllib.request.Request(url, headers=headers or {}, method="GET")
        try:
            try:
                response = self.opener.open(request, timeout=30)
            except urllib.error.HTTPError as exc:
                response = exc
            with response:
                body = response.read(MAX_BODY + 1)
                if len(body) > MAX_BODY:
                    raise ReleaseTargetError("metadata response exceeds size limit")
                status = response.status
                response_headers = {name.lower(): value for name, value in response.headers.items()}
        except (OSError, urllib.error.URLError, http.client.HTTPException, ValueError) as exc:
            if isinstance(exc, ReleaseTargetError):
                raise
            # Remote error details can contain credentials or response bodies.
            raise ReleaseTargetError(f"metadata request failed for {parsed.hostname}") from None
        if status not in (200, 404):
            raise ReleaseTargetError(f"metadata request to {parsed.hostname} returned HTTP {status}")
        return Response(status, response_headers, body)


def parse_json(response: Response):
    try:
        return json.loads(response.body)
    except (ValueError, UnicodeError, RecursionError):
        raise ReleaseTargetError("invalid JSON metadata response") from None


def github_get(client: HttpClient, url: str, headers: dict[str, str], *, allow_absent=False):
    response = client.get(url, headers)
    value = parse_json(response)
    if response.status == 404:
        if allow_absent and isinstance(value, dict) and value.get("message") == "Not Found":
            return None
        raise ReleaseTargetError("GitHub metadata was not verifiably available")
    if value is None:
        raise ReleaseTargetError("invalid GitHub metadata response")
    return value


def validate_release(value, version: str, sha: str) -> None:
    if not isinstance(value, dict):
        raise ReleaseTargetError("invalid GitHub release metadata")
    if value.get("draft") is False or value.get("published_at") is not None:
        raise ReleaseTargetError("release is already published")
    if ("published_at" not in value or value.get("draft") is not True or value.get("tag_name") != version
            or value.get("name") != version or value.get("target_commitish") != sha):
        raise ReleaseTargetError("draft release must have the exact version, title, and full commit SHA")


def check_github(client: HttpClient, version: str, sha: str, require_draft: bool) -> None:
    token = os.environ.get("GH_TOKEN")
    if require_draft and not token:
        raise ReleaseTargetError("GH_TOKEN is required to verify the draft release")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "HolyCode-release-target-guard",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = "Bearer " + token
    base = "https://api.github.com/repos/" + REPOSITORY
    release = github_get(client, base + "/releases/tags/" + version, headers, allow_absent=True)
    if release is not None:
        validate_release(release, version, sha)

    # Release-by-tag can hide drafts. Enumerate authenticated release metadata too.
    matches = []
    for page in range(1, 11):
        releases = github_get(client, base + f"/releases?per_page=100&page={page}", headers)
        if not isinstance(releases, list) or len(releases) > 100:
            raise ReleaseTargetError("invalid GitHub release list")
        for item in releases:
            if not isinstance(item, dict) or not isinstance(item.get("tag_name"), str):
                raise ReleaseTargetError("invalid GitHub release list entry")
            if item["tag_name"] == version:
                validate_release(item, version, sha)
                matches.append(item)
        if len(releases) < 100:
            break
    else:
        raise ReleaseTargetError("GitHub release list exceeds bounded pagination")
    if len(matches) > 1 or (require_draft and len(matches) != 1):
        raise ReleaseTargetError("exactly one bound draft release is required")

    ref = github_get(client, base + "/git/ref/tags/" + version, headers, allow_absent=True)
    if ref is None:
        return
    if not isinstance(ref, dict) or ref.get("ref") != "refs/tags/" + version:
        raise ReleaseTargetError("invalid GitHub tag reference")
    obj = ref.get("object")
    seen = set()
    for _ in range(10):
        if not isinstance(obj, dict) or not re.fullmatch(r"[0-9a-f]{40}", str(obj.get("sha", ""))):
            raise ReleaseTargetError("invalid GitHub tag object")
        object_sha = obj["sha"]
        if obj.get("type") == "commit":
            if object_sha != sha:
                raise ReleaseTargetError("existing tag points to a different commit")
            return
        if obj.get("type") != "tag" or object_sha in seen:
            raise ReleaseTargetError("GitHub tag cannot be resolved to a commit")
        seen.add(object_sha)
        tag = github_get(client, base + "/git/tags/" + object_sha, headers)
        if not isinstance(tag, dict) or tag.get("sha") != object_sha:
            raise ReleaseTargetError("invalid annotated tag metadata")
        obj = tag.get("object")
    raise ReleaseTargetError("GitHub tag exceeds bounded resolution")


def check_registry(client: HttpClient, host: str, token_host: str, service: str,
                   version: str, previous_digest: str | None) -> None:
    query = urllib.parse.urlencode({"service": service, "scope": "repository:" + IMAGE + ":pull"})
    response = client.get("https://" + token_host + "/token?" + query)
    value = parse_json(response)
    if response.status != 200 or not isinstance(value, dict):
        raise ReleaseTargetError("public registry pull token could not be verified")
    token = value.get("token") or value.get("access_token")
    if not isinstance(token, str) or not token or any(char.isspace() for char in token):
        raise ReleaseTargetError("invalid public registry pull token")
    headers = {"Accept": ACCEPT_MANIFEST, "Authorization": "Bearer " + token}
    base = "https://" + host + "/v2/" + IMAGE + "/manifests/"
    for alias in (version[1:], version):
        response = client.get(base + alias, headers)
        if response.status == 200:
            raise ReleaseTargetError(f"version alias {host}/{IMAGE}:{alias} already exists")
        value = parse_json(response)
        errors = value.get("errors") if isinstance(value, dict) else None
        if (not isinstance(errors, list) or not errors
                or any(not isinstance(error, dict) or error.get("code") not in
                       ("MANIFEST_UNKNOWN", "NAME_UNKNOWN") for error in errors)):
            raise ReleaseTargetError("registry version alias absence could not be verified")
    if previous_digest is not None:
        response = client.get(base + "latest", headers)
        value = parse_json(response)
        if (response.status != 200 or not isinstance(value, dict)
                or value.get("schemaVersion") != 2
                or response.headers.get("docker-content-digest") != "sha256:" + previous_digest
                or hashlib.sha256(response.body).hexdigest() != previous_digest):
            raise ReleaseTargetError(f"{host} latest differs from the expected predecessor digest")


def check_release_target(repository: str, version: str, sha: str, *,
                         require_draft: bool = False, previous_digest: str | None = None) -> None:
    if repository != REPOSITORY:
        raise ReleaseTargetError("only CoderLuii/HolyCode is supported")
    if not re.fullmatch(r"v[0-9]\.[0-9]\.[0-9]", version):
        raise ReleaseTargetError("version must match vX.Y.Z with single-digit segments")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ReleaseTargetError("sha must be a full lowercase 40-character commit SHA")
    if previous_digest is not None and not re.fullmatch(r"[0-9a-f]{64}", previous_digest):
        raise ReleaseTargetError("previous digest must be 64 lowercase hex characters without sha256:")
    client = HttpClient()
    check_github(client, version, sha, require_draft)
    check_registry(client, "registry-1.docker.io", "auth.docker.io", "registry.docker.io", version, previous_digest)
    check_registry(client, "ghcr.io", "ghcr.io", "ghcr.io", version, previous_digest)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, help="CoderLuii/HolyCode")
    parser.add_argument("--version", required=True, help="Release tag, for example v1.3.0")
    parser.add_argument("--sha", required=True, help="Exact full commit SHA")
    parser.add_argument("--require-draft", action="store_true", help="Require one exact bound draft release (uses GH_TOKEN)")
    parser.add_argument("--previous-digest", help="Require both latest aliases to match this 64-character SHA-256")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        check_release_target(args.repository, args.version, args.sha,
                             require_draft=args.require_draft, previous_digest=args.previous_digest)
    except ReleaseTargetError as exc:
        print(f"release target validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"release target validation passed: {args.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
