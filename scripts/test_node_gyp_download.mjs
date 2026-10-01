import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { join } from "node:path";

const require = createRequire(import.meta.url);
const root = "/usr/local/lib/node_modules/npm";
const gyp = require(`${root}/node_modules/node-gyp/package.json`);
const undici = require(`${root}/node_modules/undici/package.json`);
assert.equal(gyp.version, "13.0.2");
assert.equal(gyp.dependencies.undici, "^8.4.1");
assert.equal(undici.version, "8.11.2");

const directory = await mkdtemp(join(tmpdir(), "holycode-node-gyp-"));
const headerRoot = join(directory, "node-v24.21.0", "include", "node");
const tarball = join(directory, "node-v24.21.0-headers.tar.gz");
const archiveName = "node-v24.21.0-headers.tar.gz";
let server;

try {
  await mkdir(headerRoot, { recursive: true });
  await writeFile(join(headerRoot, "node.h"), "#define HOLYCODE_NODE_GYP_SMOKE 1\n");
  const tar = require(`${root}/node_modules/tar`);
  await tar.c({ gzip: true, cwd: directory, file: tarball }, ["node-v24.21.0/include/node/node.h"]);
  const archive = await readFile(tarball);
  const checksum = createHash("sha256").update(archive).digest("hex");
  const paths = [];
  server = createServer((request, response) => {
    paths.push(request.url);
    if (request.url?.endsWith(`/${archiveName}`)) {
      response.writeHead(200, { "content-type": "application/gzip" });
      response.end(archive);
    } else if (request.url?.endsWith("/SHASUMS256.txt")) {
      response.writeHead(200, { "content-type": "text/plain" });
      response.end(`${checksum}  ${archiveName}\n`);
    } else {
      response.writeHead(404);
      response.end();
    }
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const url = `http://127.0.0.1:${server.address().port}`;
  const child = spawn(process.execPath, [
    `${root}/node_modules/node-gyp/bin/node-gyp.js`,
    "install", "--target=24.21.0", `--dist-url=${url}`,
    `--devdir=${join(directory, "cache")}`,
  ], { env: { ...process.env, npm_config_offline: "true" }, stdio: ["ignore", "pipe", "pipe"] });
  let output = "";
  for (const stream of [child.stdout, child.stderr]) {
    stream.on("data", (data) => { output += data.toString(); });
  }
  let timeout;
  const exit = await Promise.race([
    new Promise((resolve) => child.once("close", resolve)),
    new Promise((_, reject) => { timeout = setTimeout(() => {
      child.kill("SIGKILL");
      reject(new Error("node-gyp download timed out"));
    }, 10000); }),
  ]);
  clearTimeout(timeout);
  assert.equal(exit, 0, output);
  assert(paths.some((path) => path?.endsWith(`/${archiveName}`)));
  assert(paths.some((path) => path?.endsWith("/SHASUMS256.txt")));
  assert.match(await readFile(join(directory, "cache", "24.21.0", "include", "node", "node.h"), "utf8"), /HOLYCODE_NODE_GYP_SMOKE/);
  console.log("node-gyp loopback header download and checksum passed");
} finally {
  if (server) await new Promise((resolve) => server.close(resolve));
  await rm(directory, { recursive: true, force: true });
}
