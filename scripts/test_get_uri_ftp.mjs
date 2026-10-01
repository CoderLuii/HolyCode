import assert from "node:assert/strict";
import { once } from "node:events";
import { createRequire } from "node:module";
import net from "node:net";
import { basename, join } from "node:path";
import { isMainThread, parentPort, workerData, Worker } from "node:worker_threads";

const DEFAULT_PM2_ROOT = "/usr/local/lib/node_modules/pm2";
const MODIFIED = "20260914010203";
const DEADLINE_MS = 5_000;

function withDeadline(promise, label, milliseconds = DEADLINE_MS) {
  let timer;
  const deadline = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`${label} exceeded ${milliseconds}ms`)), milliseconds);
  });
  return Promise.race([promise, deadline]).finally(() => clearTimeout(timer));
}

function loadInstalled(pm2Root) {
  const require = createRequire(import.meta.url);
  const getUriRoot = join(pm2Root, "node_modules", "get-uri");
  const basicFtpRoot = join(pm2Root, "node_modules", "basic-ftp");
  const getUriPackage = require(join(getUriRoot, "package.json"));
  const basicFtpPackage = require(join(basicFtpRoot, "package.json"));
  const resolvedBasicFtp = require.resolve("basic-ftp/package.json", { paths: [getUriRoot] });

  assert.equal(getUriPackage.version, "6.0.5");
  assert.equal(resolvedBasicFtp, join(basicFtpRoot, "package.json"));
  return { getUri: require(getUriRoot).getUri, basicFtpPackage };
}

async function readExactly(stream) {
  const chunks = [];
  for await (const chunk of stream) chunks.push(chunk);
  return Buffer.concat(chunks);
}

class LoopbackFtpServer {
  constructor({ files, listFallback = new Set(), malformedList = false, separateTransferHost = false }) {
    this.files = files;
    this.listFallback = listFallback;
    this.malformedList = malformedList;
    this.separateTransferHost = separateTransferHost;
    this.commands = [];
    this.logins = [];
    this.controlSockets = new Set();
    this.dataSockets = new Set();
    this.dataServers = new Set();
    this.server = net.createServer((socket) => this.handleControl(socket));
  }

  async listen() {
    this.server.listen(0, "127.0.0.1");
    await once(this.server, "listening");
    return this.server.address().port;
  }

  handleControl(socket) {
    this.controlSockets.add(socket);
    socket.setEncoding("utf8");
    socket.on("close", () => this.controlSockets.delete(socket));
    socket.on("error", () => {});
    socket.write("220 loopback fixture ready\r\n");

    let buffer = "";
    let chain = Promise.resolve();
    socket.on("data", (chunk) => {
      buffer += chunk;
      let end;
      while ((end = buffer.indexOf("\r\n")) !== -1) {
        const line = buffer.slice(0, end);
        buffer = buffer.slice(end + 2);
        chain = chain.then(() => this.handleCommand(socket, line)).catch((error) => socket.destroy(error));
      }
    });
  }

  async openDataServer() {
    const server = net.createServer();
    this.dataServers.add(server);
    const socketPromise = new Promise((resolve, reject) => {
      server.once("connection", (socket) => {
        this.dataSockets.add(socket);
        socket.on("close", () => this.dataSockets.delete(socket));
        socket.on("error", () => {});
        resolve(socket);
      });
      server.once("error", reject);
    });
    server.listen(0, "127.0.0.1");
    await once(server, "listening");
    this.pendingData = { server, socketPromise };
    return server.address().port;
  }

  async transfer(control, payload) {
    assert.ok(this.pendingData, "transfer command arrived before passive mode");
    const { server, socketPromise } = this.pendingData;
    this.pendingData = undefined;
    const socket = await withDeadline(socketPromise, "passive data connection");
    control.write("150 opening data connection\r\n");
    socket.end(payload);
    await once(socket, "finish");
    control.write("226 transfer complete\r\n");
    server.close();
    this.dataServers.delete(server);
  }

  listing() {
    if (this.malformedList) {
      const malformed = `-rw-r--r-- 1 ${"a ".repeat((48 * 1024 - 13) / 2)}!`;
      const normal = "-rw-r--r-- 1 owner group 1 Jan 1 2026 parser-target.bin";
      return `${malformed}\r\n${normal}\r\n`;
    }
    const lines = [...this.files].map(
      ([path, bytes]) => `modify=${MODIFIED};size=${bytes.length};type=file; ${basename(path)}`,
    );
    return `${lines.join("\r\n")}\r\n`;
  }

  async handleCommand(socket, line) {
    this.commands.push(line);
    const separator = line.indexOf(" ");
    const command = (separator === -1 ? line : line.slice(0, separator)).toUpperCase();
    const argument = separator === -1 ? "" : line.slice(separator + 1);

    switch (command) {
      case "USER":
        this.currentUser = argument;
        socket.write("331 password required\r\n");
        break;
      case "PASS":
        this.logins.push({ user: this.currentUser, password: argument });
        socket.write("230 logged in\r\n");
        break;
      case "FEAT":
        socket.write("211 End\r\n");
        break;
      case "OPTS":
      case "TYPE":
      case "STRU":
        socket.write("200 ok\r\n");
        break;
      case "MDTM":
        if (!this.files.has(argument)) socket.write("550 resource unavailable\r\n");
        else if (this.listFallback.has(argument)) socket.write("500 MDTM unsupported\r\n");
        else socket.write(`213 ${MODIFIED}\r\n`);
        break;
      case "EPSV": {
        if (this.separateTransferHost) {
          socket.write("500 EPSV unsupported\r\n");
          break;
        }
        const port = await this.openDataServer();
        socket.write(`229 entering extended passive mode (|||${port}|)\r\n`);
        break;
      }
      case "PASV": {
        const port = await this.openDataServer();
        const host = this.separateTransferHost ? "127,0,0,2" : "127,0,0,1";
        socket.write(`227 entering passive mode (${host},${port >> 8},${port & 255})\r\n`);
        break;
      }
      case "LIST":
        await this.transfer(socket, this.listing());
        break;
      case "RETR":
        if (!this.files.has(argument)) socket.write("550 resource unavailable\r\n");
        else await this.transfer(socket, this.files.get(argument));
        break;
      default:
        socket.write("502 command unsupported\r\n");
    }
  }

  async close() {
    for (const socket of [...this.dataSockets, ...this.controlSockets]) socket.destroy();
    for (const server of this.dataServers) server.close();
    if (this.server.listening) {
      this.server.close();
      await once(this.server, "close");
    }
  }
}

async function withServer(options, action) {
  const server = new LoopbackFtpServer(options);
  const port = await server.listen();
  try {
    return await withDeadline(action(server, port), "FTP fixture case");
  } finally {
    await server.close();
  }
}

async function runCompatibility(pm2Root) {
  const { getUri, basicFtpPackage } = loadInstalled(pm2Root);
  const specialName = "encoded file #? café.bin";
  const specialPath = `/${specialName}`;
  const fallbackPath = "/older server.bin";
  const cachePath = "/cache.bin";
  const files = new Map([
    [specialPath, Buffer.from([0, 255, 10, 13, 42, 128, 65])],
    [fallbackPath, Buffer.from("LIST fallback bytes\n")],
    [cachePath, Buffer.from("cache bytes\n")],
  ]);

  await withServer({ files, listFallback: new Set([fallbackPath]) }, async (server, port) => {
    const specialUrl = `ftp://dummy%20user:dummy%3Apass@127.0.0.1:${port}/${encodeURIComponent(specialName)}`;
    assert.deepEqual(await readExactly(await getUri(specialUrl)), files.get(specialPath));
    assert.deepEqual(server.logins[0], { user: "dummy user", password: "dummy:pass" });
    assert.ok(server.commands.includes(`MDTM ${specialPath}`));
    assert.ok(!server.commands.some((command) => command.startsWith("LIST") && command.includes(specialName)));

    const fallback = await getUri(`ftp://127.0.0.1:${port}/${encodeURIComponent(basename(fallbackPath))}`);
    assert.deepEqual(await readExactly(fallback), files.get(fallbackPath));
    assert.ok(server.commands.some((command) => command.startsWith("LIST")));

    await assert.rejects(
      getUri(`ftp://127.0.0.1:${port}/missing.bin`),
      (error) => error?.code === "ENOTFOUND",
    );

    const cacheUrl = `ftp://127.0.0.1:${port}/${basename(cachePath)}`;
    const cache = await getUri(cacheUrl);
    assert.deepEqual(await readExactly(cache), files.get(cachePath));
    await assert.rejects(getUri(cacheUrl, { cache }), (error) => error?.code === "ENOTMODIFIED");
  });

  console.log(`compatibility cases passed (get-uri 6.0.5, basic-ftp ${basicFtpPackage.version})`);
}

async function runSeparateTransferHost(pm2Root) {
  const { getUri, basicFtpPackage } = loadInstalled(pm2Root);
  const path = "/control-host-only.bin";
  const bytes = Buffer.from("separate transfer host rejected\n");
  await withServer({ files: new Map([[path, bytes]]), separateTransferHost: true }, async (_server, port) => {
    const actual = await readExactly(await getUri(`ftp://127.0.0.1:${port}${path}`));
    assert.deepEqual(actual, bytes);
  });
  console.log(`separate transfer host is ignored by default (basic-ftp ${basicFtpPackage.version})`);
}

async function runMalformedList(pm2Root) {
  const { getUri, basicFtpPackage } = loadInstalled(pm2Root);
  const path = "/parser target.bin";
  const bytes = Buffer.from("parser remained responsive\n");
  let maximumGap = 0;
  let previous = performance.now();
  const heartbeat = setInterval(() => {
    const now = performance.now();
    maximumGap = Math.max(maximumGap, now - previous);
    previous = now;
  }, 20);
  const started = performance.now();
  try {
    await withServer({ files: new Map([[path, bytes]]), listFallback: new Set([path]), malformedList: true }, async (_server, port) => {
      await assert.rejects(
        getUri(`ftp://127.0.0.1:${port}/${encodeURIComponent(basename(path))}`),
        (error) => error?.code === "ENOTFOUND",
      );
    });
  } finally {
    clearInterval(heartbeat);
  }
  const elapsed = performance.now() - started;
  assert.ok(elapsed < 1_000, `malformed LIST took ${Math.round(elapsed)}ms`);
  assert.ok(maximumGap < 500, `event-loop heartbeat stalled for ${Math.round(maximumGap)}ms`);
  return { basicFtpVersion: basicFtpPackage.version, elapsed: Math.round(elapsed), maximumGap: Math.round(maximumGap) };
}

async function runParserWorker(pm2Root) {
  const worker = new Worker(new URL(import.meta.url), { workerData: { mode: "parser-worker", pm2Root } });
  try {
    const result = await withDeadline(new Promise((resolve, reject) => {
      worker.once("message", (message) => message.ok ? resolve(message.result) : reject(new Error(message.error)));
      worker.once("error", reject);
      worker.once("exit", (code) => {
        if (code !== 0) reject(new Error(`parser worker exited with code ${code}`));
      });
    }), "malformed LIST worker", 6_000);
    console.log(`malformed LIST stayed responsive with basic-ftp ${result.basicFtpVersion} (${result.elapsed}ms total, ${result.maximumGap}ms max heartbeat gap)`);
  } finally {
    await worker.terminate();
  }
}

async function main() {
  const mode = process.argv[2] ?? "all";
  const pm2Root = process.argv[3] ?? DEFAULT_PM2_ROOT;
  assert.ok(["all", "compat", "fixed", "transfer-host", "parser"].includes(mode), `unknown mode: ${mode}`);

  if (mode === "all" || mode === "fixed") {
    assert.equal(loadInstalled(pm2Root).basicFtpPackage.version, "6.2.1");
  }

  if (mode === "all" || mode === "compat") await runCompatibility(pm2Root);
  if (mode === "all" || mode === "fixed" || mode === "transfer-host") await runSeparateTransferHost(pm2Root);
  if (mode === "all" || mode === "fixed" || mode === "parser") await runParserWorker(pm2Root);
}

if (!isMainThread && workerData?.mode === "parser-worker") {
  runMalformedList(workerData.pm2Root).then(
    (result) => parentPort.postMessage({ ok: true, result }),
    (error) => parentPort.postMessage({ ok: false, error: error?.stack ?? String(error) }),
  );
} else {
  main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}
