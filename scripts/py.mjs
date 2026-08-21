#!/usr/bin/env node
/**
 * Cross-platform Python launcher for Pinterest Video Downloader.
 * Bootstraps a .venv from requirements.txt and runs the requested target,
 * so the project works with a plain `npm install` + `npm run dev`.
 *
 * Usage:
 *   node scripts/py.mjs setup           # create/refresh .venv from requirements.txt
 *   node scripts/py.mjs app [--debug]   # run the Flask server (FLASK_DEBUG=1 with --debug)
 *   node scripts/py.mjs cli             # run the CLI downloader
 *   node scripts/py.mjs audit           # CVE-check installed packages with pip-audit
 */
import { spawn, spawnSync } from "node:child_process";
import { existsSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const VENV = path.join(ROOT, ".venv");
const REQ_FILE = path.join(ROOT, "requirements.txt");
const STAMP = path.join(VENV, ".deps-ok");
const VENV_PY = process.platform === "win32"
  ? path.join(VENV, "Scripts", "python.exe")
  : path.join(VENV, "bin", "python");

const log = (msg) => console.log(`[pvd] ${msg}`);

function findSystemPython() {
  if (process.env.PYTHON) return [process.env.PYTHON, []];
  const candidates = process.platform === "win32"
    ? [["py", ["-3"]], ["python", []], ["python3", []]]
    : [["python3", []], ["python", []]];
  for (const [cmd, args] of candidates) {
    try {
      const probe = spawnSync(cmd, [...args, "--version"], { stdio: "ignore" });
      if (probe.status === 0) return [cmd, args];
    } catch { /* keep looking */ }
  }
  return null;
}

function run(cmd, args) {
  const res = spawnSync(cmd, args, { stdio: "inherit", cwd: ROOT });
  if (res.status !== 0) {
    console.error(`[pvd] command failed (exit ${res.status}): ${cmd} ${args.join(" ")}`);
    process.exit(res.status ?? 1);
  }
}

function setup() {
  const py = findSystemPython();
  if (!py) {
    console.error("[pvd] Python 3 not found. Install Python 3.10+ (and set $PYTHON if needed).");
    process.exit(1);
  }
  if (!existsSync(VENV_PY)) {
    log(`creating virtualenv at ${path.relative(ROOT, VENV)} ...`);
    run(py[0], [...py[1], "-m", "venv", VENV]);
  }
  log("installing pinned dependencies from requirements.txt ...");
  run(VENV_PY, ["-m", "pip", "install", "--disable-pip-version-check", "-q",
                "-r", REQ_FILE]);
  writeFileSync(STAMP, new Date().toISOString());
  log("environment ready ✓");
}

function ensureEnv() {
  const fresh = existsSync(VENV_PY) && existsSync(STAMP)
    && statSync(STAMP).mtimeMs >= statSync(REQ_FILE).mtimeMs;
  if (!fresh) setup();
}

function runPython(script, extraArgs = [], env = {}) {
  ensureEnv();
  const child = spawn(VENV_PY, [script, ...extraArgs], {
    stdio: "inherit",
    cwd: ROOT,
    env: { ...process.env, ...env },
  });
  const forward = (sig) => child.kill(sig);
  process.on("SIGINT", () => forward("SIGINT"));
  process.on("SIGTERM", () => forward("SIGTERM"));
  child.on("exit", (code, signal) => process.exit(signal ? 1 : (code ?? 0)));
}

const [command, ...rest] = process.argv.slice(2);

switch (command) {
  case "setup":
    setup();
    break;

  case "app":
    runPython("app.py", [], { FLASK_DEBUG: rest.includes("--debug") ? "1" : "0" });
    break;

  case "cli":
    runPython("main.py");
    break;

  case "audit":
    ensureEnv();
    log("ensuring pip-audit ...");
    run(VENV_PY, ["-m", "pip", "install", "--disable-pip-version-check", "-q", "pip-audit"]);
    log("auditing installed packages for known CVEs ...");
    run(VENV_PY, ["-m", "pip_audit"]);
    break;

  default:
    console.error(`[pvd] unknown command: ${command ?? "(none)"}`);
    console.error("usage: node scripts/py.mjs <setup|app|cli|audit> [--debug]");
    process.exit(1);
}
