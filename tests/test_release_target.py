import contextlib
import hashlib
import io
import json
import ssl
import unittest
import urllib.error
from unittest import mock

from scripts import check_release_target as guard


SHA = "a" * 40
OTHER_SHA = "b" * 40
VERSION = "v1.3.0"
REPOSITORY = "CoderLuii/HolyCode"
API = "https://api.github.com/repos/CoderLuii/HolyCode"
RELEASE_URL = API + "/releases/tags/v1.3.0"
RELEASE_LIST_URL = API + "/releases?per_page=100&page=1"
TAG_URL = API + "/git/ref/tags/v1.3.0"
REGISTRIES = ("registry-1.docker.io", "ghcr.io")
MANIFEST = json.dumps({"schemaVersion": 2, "mediaType": "application/vnd.oci.image.index.v1+json", "manifests": []}).encode()
DIGEST = hashlib.sha256(MANIFEST).hexdigest()


def encoded(value):
    return json.dumps(value).encode()


class Response:
    def __init__(self, status=200, value=None, headers=None, body=None):
        self.status = status
        self.headers = headers or {}
        self.body = encoded(value) if body is None else body

    def read(self, limit):
        return self.body[:limit]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class ReleaseTargetTests(unittest.TestCase):
    def setUp(self):
        self.routes = {
            RELEASE_URL: Response(404, {"message": "Not Found"}),
            RELEASE_LIST_URL: Response(value=[]),
            TAG_URL: Response(404, {"message": "Not Found"}),
            "https://auth.docker.io/token?service=registry.docker.io&scope=repository%3Acoderluii%2Fholycode%3Apull": Response(value={"token": "hub-public-pull-token"}),
            "https://ghcr.io/token?service=ghcr.io&scope=repository%3Acoderluii%2Fholycode%3Apull": Response(value={"token": "ghcr-public-pull-token"}),
        }
        for host in REGISTRIES:
            for alias in ("1.3.0", "v1.3.0"):
                self.routes[self.manifest_url(host, alias)] = Response(404, {"errors": [{"code": "MANIFEST_UNKNOWN"}]})
            self.routes[self.manifest_url(host, "latest")] = Response(
                body=MANIFEST, headers={"Docker-Content-Digest": "sha256:" + DIGEST}
            )
        self.requests = []
        self.opener = mock.Mock()
        self.opener.open.side_effect = self.open
        self.patch = mock.patch.object(guard.urllib.request, "build_opener", return_value=self.opener)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.env_patch = mock.patch.dict("os.environ", {"GH_TOKEN": "test-github-token"})
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    @staticmethod
    def manifest_url(host, alias):
        return f"https://{host}/v2/coderluii/holycode/manifests/{alias}"

    def open(self, request, timeout):
        self.requests.append(request)
        self.assertEqual(request.get_method(), "GET")
        self.assertGreater(timeout, 0)
        if request.full_url not in self.routes:
            self.fail(f"unexpected network request: {request.full_url}")
        value = self.routes[request.full_url]
        if isinstance(value, Exception):
            raise value
        return value

    def check(self, **kwargs):
        guard.check_release_target(REPOSITORY, VERSION, SHA, **kwargs)

    def draft(self, **changes):
        value = {"tag_name": VERSION, "name": VERSION, "target_commitish": SHA,
                 "draft": True, "published_at": None}
        value.update(changes)
        self.routes[RELEASE_URL] = Response(value=value)
        self.routes[RELEASE_LIST_URL] = Response(value=[value])

    def test_absent_release_and_version_aliases_are_safe(self):
        self.check()
        urls = {request.full_url for request in self.requests}
        for host in REGISTRIES:
            for alias in ("1.3.0", "v1.3.0"):
                self.assertIn(self.manifest_url(host, alias), urls)

    def test_published_release_always_blocks(self):
        self.draft(draft=False, published_at="2026-11-01T00:00:00Z")
        with self.assertRaisesRegex(guard.ReleaseTargetError, "published"):
            self.check()

    def test_published_timestamp_blocks_inconsistent_draft(self):
        self.draft(published_at="2026-11-01T00:00:00Z")
        with self.assertRaises(guard.ReleaseTargetError):
            self.check()

    def test_incomplete_draft_metadata_blocks(self):
        self.draft()
        value = json.loads(self.routes[RELEASE_URL].body)
        del value["published_at"]
        self.routes[RELEASE_URL] = Response(value=value)
        with self.assertRaises(guard.ReleaseTargetError):
            self.check()

    def test_exact_bound_draft_is_safe(self):
        self.draft()
        self.routes[RELEASE_URL] = Response(404, {"message": "Not Found"})
        self.check(require_draft=True)

    def test_anonymous_preflight_is_safe_but_cannot_prove_draft(self):
        with mock.patch.dict(guard.os.environ, {}, clear=True):
            self.check()
            self.draft()
            with self.assertRaises(guard.ReleaseTargetError):
                self.check(require_draft=True)

    def test_release_list_detects_published_tag_even_if_tag_endpoint_is_absent(self):
        self.draft(draft=False, published_at="2026-11-01T00:00:00Z")
        self.routes[RELEASE_URL] = Response(404, {"message": "Not Found"})
        with self.assertRaises(guard.ReleaseTargetError):
            self.check()

    def test_release_list_paginates_and_rejects_unbounded_or_invalid_data(self):
        unrelated = {"tag_name": "v1.2.9"}
        self.routes[RELEASE_LIST_URL] = Response(value=[unrelated] * 100)
        second_page = API + "/releases?per_page=100&page=2"
        self.routes[second_page] = Response(value=[])
        self.check()
        self.assertIn(second_page, {request.full_url for request in self.requests})
        self.routes[second_page] = Response(value={})
        with self.assertRaises(guard.ReleaseTargetError):
            self.check()
        for page in range(2, 11):
            self.routes[API + f"/releases?per_page=100&page={page}"] = Response(value=[unrelated] * 100)
        with self.assertRaises(guard.ReleaseTargetError):
            self.check()

    def test_draft_requires_exact_tag_name_title_and_full_sha(self):
        for changes in ({"tag_name": "v1.2.9"}, {"name": "HolyCode v1.3.0"},
                        {"target_commitish": "main"}, {"target_commitish": OTHER_SHA},
                        {"target_commitish": SHA[:7]}, {"draft": "true"}):
            with self.subTest(changes=changes):
                self.draft(**changes)
                with self.assertRaises(guard.ReleaseTargetError):
                    self.check()

    def test_promotion_requires_existing_draft(self):
        with self.assertRaisesRegex(guard.ReleaseTargetError, "draft"):
            self.check(require_draft=True)

    def test_existing_version_alias_blocks_in_either_registry(self):
        for host in REGISTRIES:
            for alias in ("1.3.0", "v1.3.0"):
                with self.subTest(host=host, alias=alias):
                    url = self.manifest_url(host, alias)
                    missing = self.routes[url]
                    self.routes[url] = Response(body=MANIFEST)
                    with self.assertRaisesRegex(guard.ReleaseTargetError, "already exists"):
                        self.check()
                    self.routes[url] = missing

    def test_second_check_detects_release_published_during_build(self):
        self.check()
        self.draft(draft=False, published_at="2026-11-01T00:00:00Z")
        with self.assertRaises(guard.ReleaseTargetError):
            self.check(require_draft=True, previous_digest=DIGEST)

    def test_second_check_detects_alias_created_during_build(self):
        self.check()
        self.draft()
        self.routes[self.manifest_url("ghcr.io", "1.3.0")] = Response(body=MANIFEST)
        with self.assertRaises(guard.ReleaseTargetError):
            self.check(require_draft=True, previous_digest=DIGEST)

    def test_both_latest_digests_must_match_expected_predecessor(self):
        self.draft()
        self.check(require_draft=True, previous_digest=DIGEST)
        for host in REGISTRIES:
            with self.subTest(host=host):
                url = self.manifest_url(host, "latest")
                original = self.routes[url]
                self.routes[url] = Response(body=MANIFEST, headers={"Docker-Content-Digest": "sha256:" + "c" * 64})
                with self.assertRaises(guard.ReleaseTargetError):
                    self.check(require_draft=True, previous_digest=DIGEST)
                self.routes[url] = original

    def test_missing_or_unverifiable_latest_blocks(self):
        for response in (Response(404, {"errors": [{"code": "MANIFEST_UNKNOWN"}]}),
                         Response(body=MANIFEST),
                         Response(body=b"{}", headers={"Docker-Content-Digest": "sha256:" + DIGEST}),
                         Response(body=b"invalid", headers={"Docker-Content-Digest": "sha256:" + DIGEST})):
            with self.subTest(response=response):
                self.routes[self.manifest_url("ghcr.io", "latest")] = response
                with self.assertRaises(guard.ReleaseTargetError):
                    self.check(previous_digest=DIGEST)

    def test_lightweight_tag_must_point_to_exact_sha(self):
        self.routes[TAG_URL] = Response(value={"ref": "refs/tags/" + VERSION, "object": {"type": "commit", "sha": SHA}})
        self.check()
        self.routes[TAG_URL] = Response(value={"ref": "refs/tags/" + VERSION, "object": {"type": "commit", "sha": OTHER_SHA}})
        with self.assertRaisesRegex(guard.ReleaseTargetError, "tag"):
            self.check()

    def test_annotated_tag_is_peeled_and_checked(self):
        tag_sha = "c" * 40
        self.routes[TAG_URL] = Response(value={"ref": "refs/tags/" + VERSION, "object": {"type": "tag", "sha": tag_sha}})
        self.routes[API + "/git/tags/" + tag_sha] = Response(value={"sha": tag_sha, "object": {"type": "commit", "sha": SHA}})
        self.check()
        self.routes[API + "/git/tags/" + tag_sha] = Response(value={"sha": tag_sha, "object": {"type": "commit", "sha": OTHER_SHA}})
        with self.assertRaises(guard.ReleaseTargetError):
            self.check()

    def test_tag_cycles_unknown_types_and_missing_objects_block(self):
        tag_sha = "c" * 40
        for obj in ({"type": "tree", "sha": SHA}, {"type": "commit"}, {"type": "tag", "sha": tag_sha}):
            with self.subTest(obj=obj):
                self.routes[TAG_URL] = Response(value={"ref": "refs/tags/" + VERSION, "object": obj})
                self.routes[API + "/git/tags/" + tag_sha] = Response(value={"sha": tag_sha, "object": obj})
                with self.assertRaises(guard.ReleaseTargetError):
                    self.check()

    def test_tag_resolution_is_bounded(self):
        self.routes[TAG_URL] = Response(value={"ref": "refs/tags/" + VERSION, "object": {"type": "tag", "sha": f"{1:040x}"}})
        for number in range(1, 21):
            self.routes[API + "/git/tags/" + f"{number:040x}"] = Response(value={"sha": f"{number:040x}", "object": {"type": "tag", "sha": f"{number + 1:040x}"}})
        with self.assertRaises(guard.ReleaseTargetError):
            self.check()
        self.assertLess(len(self.requests), 20)

    def test_auth_rate_limit_server_and_redirect_statuses_never_mean_absent(self):
        token_url = next(url for url in self.routes if url.startswith("https://auth.docker.io/"))
        for url in (RELEASE_URL, RELEASE_LIST_URL, TAG_URL, token_url,
                    self.manifest_url("ghcr.io", "1.3.0")):
            original = self.routes[url]
            for status in (301, 302, 307, 308, 401, 403, 429, 500, 503):
                with self.subTest(url=url, status=status):
                    self.routes[url] = Response(status, {"message": "Not Found"})
                    with self.assertRaises(guard.ReleaseTargetError):
                        self.check()
            self.routes[url] = original

    def test_only_recognized_not_found_bodies_count_as_absent(self):
        for url in (RELEASE_URL, TAG_URL, self.manifest_url("ghcr.io", "1.3.0")):
            original = self.routes[url]
            for body in (b"not json", b"{}", b"[]", b"null", encoded({"errors": [{"code": "UNAUTHORIZED"}]})):
                with self.subTest(url=url, body=body):
                    self.routes[url] = Response(404, body=body)
                    with self.assertRaises(guard.ReleaseTargetError):
                        self.check()
            self.routes[url] = original

    def test_network_tls_timeout_errors_fail_closed_without_echoing_secrets(self):
        for error in (urllib.error.URLError("private-token-value"),
                      ssl.SSLError("private-token-value"), TimeoutError("private-token-value")):
            with self.subTest(error=error):
                self.routes[RELEASE_URL] = error
                with self.assertRaises(guard.ReleaseTargetError) as caught:
                    self.check()
                self.assertNotIn("private-token-value", str(caught.exception))

    def test_http_error_404_body_is_checked(self):
        self.routes[RELEASE_URL] = urllib.error.HTTPError(RELEASE_URL, 404, "Not Found", {}, io.BytesIO(encoded({"message": "Not Found"})))
        self.check()

    def test_invalid_success_json_or_token_blocks(self):
        token_url = next(url for url in self.routes if url.startswith("https://auth.docker.io/"))
        for url in (RELEASE_URL, TAG_URL, token_url):
            original = self.routes[url]
            for body in (b"invalid", b"[]", b"null", b"{}"):
                with self.subTest(url=url, body=body):
                    self.routes[url] = Response(body=body)
                    with self.assertRaises(guard.ReleaseTargetError):
                        self.check()
            self.routes[url] = original

    def test_github_token_is_sent_only_to_github(self):
        with mock.patch.dict(guard.os.environ, {"GH_TOKEN": "private-github-token"}):
            self.check()
        for request in self.requests:
            auth = request.get_header("Authorization", "")
            if request.full_url.startswith("https://api.github.com/"):
                self.assertEqual(auth, "Bearer private-github-token")
            else:
                self.assertNotIn("private-github-token", auth)

    def test_unofficial_or_insecure_urls_are_rejected_before_network(self):
        client = guard.HttpClient()
        for url in ("http://api.github.com/repos/CoderLuii/HolyCode", "https://api.github.com.evil.test/", "https://user:secret@api.github.com/", "https://api.github.com:8443/", "https://example.test/"):
            with self.subTest(url=url):
                with self.assertRaises(guard.ReleaseTargetError):
                    client.get(url)
        self.assertEqual(self.requests, [])

    def test_redirect_handler_never_follows_redirect(self):
        handler = guard.NoRedirect()
        request = guard.urllib.request.Request(RELEASE_URL)
        self.assertIsNone(handler.redirect_request(request, None, 302, "redirect", {}, "https://evil.test/"))

    def test_client_uses_verified_tls_and_installs_redirect_blocker(self):
        guard.HttpClient()
        handlers = guard.urllib.request.build_opener.call_args.args
        self.assertTrue(any(isinstance(handler, guard.NoRedirect) for handler in handlers))
        contexts = [handler._context for handler in handlers if isinstance(handler, guard.urllib.request.HTTPSHandler)]
        self.assertEqual(len(contexts), 1)
        self.assertEqual(contexts[0].verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(contexts[0].check_hostname)

    def test_oversized_metadata_response_blocks(self):
        self.routes[RELEASE_URL] = Response(body=b" " * (guard.MAX_BODY + 1))
        with self.assertRaisesRegex(guard.ReleaseTargetError, "size limit"):
            self.check()

    def test_invalid_arguments_fail_before_network(self):
        for kwargs in ({"repository": "someone/else"}, {"version": "v1.30.0"},
                       {"version": "../latest"}, {"sha": SHA[:7]},
                       {"sha": "g" * 40}, {"previous_digest": "sha256:" + DIGEST}):
            with self.subTest(kwargs=kwargs):
                args = {"repository": REPOSITORY, "version": VERSION, "sha": SHA}
                args.update(kwargs)
                with self.assertRaises(guard.ReleaseTargetError):
                    guard.check_release_target(**args)
        self.assertEqual(self.requests, [])

    def test_cli_reports_safe_or_refused_without_token_or_response_body(self):
        argv = ["--repository", REPOSITORY, "--version", VERSION, "--sha", SHA]
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            self.assertEqual(guard.main(argv), 0)
            self.routes[RELEASE_URL] = Response(403, {"message": "private-response-secret"})
            self.assertEqual(guard.main(argv), 1)
        self.assertIn("passed", output.getvalue())
        self.assertIn("failed", errors.getvalue())
        self.assertNotIn("private-response-secret", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
