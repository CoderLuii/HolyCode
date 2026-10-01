#!/usr/bin/env python3
"""Exercise pip's vendored urllib3 against local index, TLS, and proxy peers."""

import base64
import hashlib
import http.server
import io
import os
import pathlib
import select
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import zipfile

from pip._vendor import requests, urllib3


assert urllib3.__version__ == "2.8.0"
assert requests.adapters.PoolManager is urllib3.PoolManager
assert requests.adapters.PoolManager.__module__.replace(".", "/").startswith("pip/_vendor/urllib3/")


class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True


def serve(handler, *, tls=None):
    server = Server(("127.0.0.1", 0), handler)
    if tls:
        server.socket = tls.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def close(*servers):
    for server in servers:
        server.shutdown()
        server.server_close()


def certificate(directory, name):
    key = directory / f"{name}.key"
    cert = directory / f"{name}.crt"
    subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
         "-keyout", str(key), "-out", str(cert), "-subj", "/CN=localhost",
         "-addext", "subjectAltName=DNS:localhost"],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(cert, key)
    client_context = ssl.create_default_context(cafile=str(cert))
    client_context.load_cert_chain(cert, key)
    return server_context, client_context, cert


def wheel_bytes():
    filename = "holycode_vendor_probe-1.0-py3-none-any.whl"
    info = "holycode_vendor_probe-1.0.dist-info"
    entries = {
        "holycode_vendor_probe/__init__.py": 'VALUE = "installed"\n',
        f"{info}/METADATA": "Metadata-Version: 2.1\nName: holycode-vendor-probe\nVersion: 1.0\n",
        f"{info}/WHEEL": "Wheel-Version: 1.0\nGenerator: holycode-smoke\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
    }
    record = []
    for path, content in entries.items():
        data = content.encode()
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        record.append(f"{path},sha256={digest},{len(data)}")
    record.append(f"{info}/RECORD,,")
    entries[f"{info}/RECORD"] = "\n".join(record) + "\n"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path, content in entries.items():
            archive.writestr(path, content)
    return filename, buffer.getvalue()


def test_pip_index_and_install(directory):
    filename, wheel = wheel_bytes()
    expected_auth = "Basic " + base64.b64encode(b"probe:local-only").decode()

    class Index(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.headers.get("Authorization") != expected_auth:
                self.send_response(401)
                self.send_header("WWW-Authenticate", 'Basic realm="local"')
                self.end_headers()
                return
            if self.path == "/simple/holycode-vendor-probe/":
                body = f'<a href="/{filename}">{filename}</a>\n'.encode()
                content_type = "text/html"
            elif self.path == f"/{filename}":
                body = wheel
                content_type = "application/octet-stream"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    server = serve(Index)
    try:
        index = f"http://probe:local-only@127.0.0.1:{server.server_port}/simple/"
        environment = {**os.environ, "PIP_INDEX_URL": index, "PIP_DISABLE_PIP_VERSION_CHECK": "1"}
        command = [sys.executable, "-m", "pip"]
        subprocess.run(command + ["debug", "--verbose"], env=environment, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=15)
        try:
            subprocess.run(command + ["index", "versions", "holycode-vendor-probe", "--retries", "0", "--timeout", "3", "--quiet"],
                           env=environment, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=15)
        except subprocess.CalledProcessError as error:
            raise AssertionError(error.stderr.decode().replace("probe:local-only", "<local-auth>")) from error
        target = directory / "installed"
        subprocess.run(command + ["install", "holycode-vendor-probe==1.0", "--target", str(target),
                                  "--no-deps", "--no-cache-dir", "--retries", "0", "--timeout", "3", "--quiet"],
                       env=environment, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=15)
        assert (target / "holycode_vendor_probe" / "__init__.py").read_text() == 'VALUE = "installed"\n'
        downloads = directory / "downloads"
        subprocess.run(command + ["download", "holycode-vendor-probe==1.0", "--dest", str(downloads),
                                  "--no-deps", "--no-cache-dir", "--retries", "0", "--timeout", "3", "--quiet"],
                       env=environment, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=15)
        assert (downloads / filename).read_bytes() == wheel
        local_wheel = directory / filename
        local_wheel.write_bytes(wheel)
        subprocess.run(command + ["install", "--no-index", "--find-links", str(directory),
                                  "holycode-vendor-probe==1.0", "--target", str(directory / "offline"),
                                  "--no-deps", "--quiet"],
                       env={**environment, "PIP_INDEX_URL": ""}, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=15)
        assert (directory / "offline" / "holycode_vendor_probe" / "__init__.py").is_file()
        project = directory / "pep517"
        project.mkdir()
        (project / "pyproject.toml").write_text(
            '[build-system]\nrequires = ["setuptools"]\nbuild-backend = "setuptools.build_meta"\n'
        )
        (project / "setup.cfg").write_text(
            '[metadata]\nname = holycode-pep517-probe\nversion = 1.0\n'
        )
        (project / "probe.py").write_text('VALUE = "pep517"\n')
        subprocess.run(command + ["wheel", "--no-index", "--no-deps", "--no-build-isolation",
                                  "--wheel-dir", str(directory / "built"), str(project)],
                       env=environment, check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.PIPE, timeout=15)
        assert list((directory / "built").glob("holycode_pep517_probe-1.0-*.whl"))
    finally:
        close(server)


def test_tls_and_proxy(directory):
    target_tls, target_client, target_cert = certificate(directory, "target")
    proxy_tls, proxy_client, proxy_cert = certificate(directory, "proxy")
    target_tls.load_verify_locations(cafile=str(target_cert))
    target_tls.verify_mode = ssl.CERT_REQUIRED
    proxy_tls.load_verify_locations(cafile=str(proxy_cert))
    proxy_tls.verify_mode = ssl.CERT_REQUIRED
    target_settings = (target_client.verify_mode, target_client.check_hostname)
    proxy_settings = (proxy_client.verify_mode, proxy_client.check_hostname)

    class Target(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            body = b"target tls ok"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    target = serve(Target, tls=target_tls)
    target_url = f"https://localhost:{target.server_port}/"

    class Proxy(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            body = b"http proxy ok"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_CONNECT(self):
            upstream = socket.create_connection(("127.0.0.1", target.server_port), timeout=3)
            self.send_response(200, "Connection established")
            self.end_headers()
            self.connection.settimeout(3)
            try:
                while True:
                    readable, _, _ = select.select([self.connection, upstream], [], [], 3)
                    if not readable:
                        break
                    for source in readable:
                        chunk = source.recv(65536)
                        if not chunk:
                            return
                        (upstream if source is self.connection else self.connection).sendall(chunk)
            finally:
                upstream.close()

        def log_message(self, *_):
            pass

    http_proxy = serve(Proxy)
    https_proxy = serve(Proxy, tls=proxy_tls)
    try:
        secure = urllib3.PoolManager(ssl_context=target_client, retries=False)
        assert secure.request("GET", target_url, timeout=urllib3.Timeout(total=3)).data == b"target tls ok"
        try:
            urllib3.PoolManager(retries=False).request("GET", target_url, timeout=urllib3.Timeout(total=3))
        except urllib3.exceptions.SSLError:
            pass
        else:
            raise AssertionError("untrusted target certificate accepted")
        try:
            secure.request("GET", f"https://127.0.0.1:{target.server_port}/", timeout=urllib3.Timeout(total=3))
        except urllib3.exceptions.SSLError:
            pass
        else:
            raise AssertionError("wrong target hostname accepted")
        proxied = urllib3.ProxyManager(f"http://127.0.0.1:{http_proxy.server_port}", retries=False)
        assert proxied.request("GET", "http://invalid.example/", timeout=urllib3.Timeout(total=3)).data == b"http proxy ok"
        tunneled = urllib3.ProxyManager(
            f"https://localhost:{https_proxy.server_port}",
            proxy_ssl_context=proxy_client, ssl_context=target_client, retries=False,
        )
        assert tunneled.request("GET", target_url, timeout=urllib3.Timeout(total=3)).data == b"target tls ok"
        forwarded = urllib3.ProxyManager(
            f"https://localhost:{https_proxy.server_port}",
            proxy_ssl_context=proxy_client, ssl_context=target_client,
            use_forwarding_for_https=True, retries=False,
        )
        assert forwarded.request("GET", target_url, timeout=urllib3.Timeout(total=3)).data == b"http proxy ok"
        try:
            urllib3.ProxyManager(
                f"https://localhost:{https_proxy.server_port}",
                proxy_ssl_context=target_client, ssl_context=target_client, retries=False,
            ).request("GET", target_url, timeout=urllib3.Timeout(total=3))
        except urllib3.exceptions.ProxyError:
            pass
        else:
            raise AssertionError("untrusted HTTPS proxy certificate accepted")
        assert (target_client.verify_mode, target_client.check_hostname) == target_settings
        assert (proxy_client.verify_mode, proxy_client.check_hostname) == proxy_settings
    finally:
        close(http_proxy, https_proxy, target)


def test_oversized_chunk_header():
    class Chunked(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            try:
                self.wfile.write(b"f" * 65537 + b"\r\n")
                self.wfile.flush()
                time.sleep(2)
            except BrokenPipeError:
                pass

        def log_message(self, *_):
            pass

    server = serve(Chunked)
    try:
        for method in ("read_chunked", "stream"):
            response = urllib3.PoolManager(retries=False).request(
                "GET", f"http://127.0.0.1:{server.server_port}/",
                timeout=urllib3.Timeout(total=1), preload_content=False,
            )
            started = time.monotonic()
            try:
                list(getattr(response, method)())
            except urllib3.exceptions.ProtocolError as error:
                assert str(error) == "Response chunk size line exceeded maximum allowed length"
                assert time.monotonic() - started < 1
            else:
                raise AssertionError(f"oversized chunk header accepted by {method}")
            finally:
                response.close()
    finally:
        close(server)


with tempfile.TemporaryDirectory(prefix="holycode-pip-vendor-") as directory:
    root = pathlib.Path(directory)
    test_pip_index_and_install(root)
    test_tls_and_proxy(root)
    test_oversized_chunk_header()
print("pip vendored urllib3 index, install, TLS, proxy, and chunk fixtures passed")
