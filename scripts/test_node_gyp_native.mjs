import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { constants } from "node:fs";
import { access, mkdtemp, rm, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { join } from "node:path";

const require = createRequire(import.meta.url);
const npmRoot = "/usr/local/lib/node_modules/npm";
const nodeGypRoot = join(npmRoot, "node_modules", "node-gyp");
const undiciRoot = join(npmRoot, "node_modules", "undici");
const npmPackage = require(join(npmRoot, "package.json"));
const nodeGypPackage = require(join(nodeGypRoot, "package.json"));
const undiciPackagePath = require.resolve("undici/package.json", { paths: [nodeGypRoot] });
const undiciPackage = require(undiciPackagePath);

assert.equal(npmPackage.version, "12.2.0");
assert.equal(npmPackage.dependencies["node-gyp"], "^13.0.0");
assert.equal(nodeGypPackage.version, "13.0.2");
assert.equal(nodeGypPackage.dependencies.undici, "^8.4.1");
assert.equal(undiciPackagePath, join(undiciRoot, "package.json"));
assert.equal(undiciPackage.version, "8.11.2");
await access("/usr/local/include/node/node_api.h", constants.R_OK);
await access("/usr/local/include/node/common.gypi", constants.R_OK);
await access("/usr/bin/g++", constants.X_OK);

const packageJson = `${JSON.stringify({
  name: "holycode-node-gyp-native-fixture",
  version: "1.0.0",
  private: true,
  gypfile: true,
})}\n`;
const bindingGyp = `${JSON.stringify({
  targets: [{ target_name: "holycode_native", sources: ["addon.cc"] }],
}, null, 2)}\n`;
const addon = `#include <node_api.h>

static napi_value Answer(napi_env env, napi_callback_info info) {
  napi_value result;
  if (napi_create_int32(env, 42, &result) != napi_ok) return nullptr;
  return result;
}

static napi_value Init(napi_env env, napi_value exports) {
  napi_value answer;
  if (napi_create_function(env, "answer", NAPI_AUTO_LENGTH, Answer, nullptr, &answer) != napi_ok) return nullptr;
  if (napi_set_named_property(env, exports, "answer", answer) != napi_ok) return nullptr;
  return exports;
}

NAPI_MODULE(NODE_GYP_MODULE_NAME, Init)
`;

function killProcessGroup(child) {
  try {
    process.kill(-child.pid, "SIGKILL");
  } catch {
    child.kill("SIGKILL");
  }
}

function install(directory) {
  return new Promise((resolve, reject) => {
    const child = spawn("/usr/local/bin/npm", [
      "install",
      "--offline",
      "--no-audit",
      "--no-fund",
      "--foreground-scripts",
    ], {
      cwd: directory,
      detached: true,
      env: {
        ...process.env,
        HOME: directory,
        npm_config_cache: join(directory, ".npm"),
        // npm 12 rejects unknown CLI config flags but forwards this to node-gyp.
        npm_config_nodedir: "/usr/local",
        npm_config_update_notifier: "false",
      },
      stdio: ["ignore", "pipe", "pipe"],
    });
    let output = "";
    let settled = false;
    let timeout;
    const finish = (error, result) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      if (error) reject(error);
      else resolve(result);
    };
    const capture = (chunk) => {
      output += chunk.toString();
      if (output.length > 1024 * 1024) {
        killProcessGroup(child);
        finish(new Error("npm install output exceeded 1 MiB"));
      }
    };
    child.stdout.on("data", capture);
    child.stderr.on("data", capture);
    child.once("error", (error) => finish(error));
    child.once("close", (code, signal) => finish(undefined, { code, signal, output }));
    timeout = setTimeout(() => {
      killProcessGroup(child);
      finish(new Error("npm install timed out after 45 seconds"));
    }, 45_000);
  });
}

const directory = await mkdtemp(join(tmpdir(), "holycode-node-gyp-native-"));
try {
  await Promise.all([
    writeFile(join(directory, "package.json"), packageJson),
    writeFile(join(directory, "binding.gyp"), bindingGyp),
    writeFile(join(directory, "addon.cc"), addon),
  ]);

  const result = await install(directory);
  assert.equal(result.code, 0, result.output);
  assert.equal(result.signal, null, result.output);
  assert.match(result.output, /gyp info using node-gyp@13\.0\.2/);
  assert.match(result.output, /CXX\(target\)/);

  const binary = join(directory, "build", "Release", "holycode_native.node");
  await access(binary, constants.R_OK);
  const native = require(binary);
  assert.equal(native.answer(), 42);
} finally {
  await rm(directory, { recursive: true, force: true });
}

await assert.rejects(access(directory), (error) => error?.code === "ENOENT");
console.log("npm-owned node-gyp native N-API build passed offline");
