#!/usr/bin/env node
/**
 * Zero-dependency static server for the agent WebUIs.
 *   node webui/server.mjs           # serves on http://localhost:4321
 *   PORT=8080 node webui/server.mjs
 *
 * Exposes /api/git-committer for the Track 3 demo, plus clear stub responses
 * for the other agent consoles until their backends are connected.
 */
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join, normalize } from "node:path";
import { existsSync } from "node:fs";
import { spawn } from "node:child_process";

const DIR = dirname(fileURLToPath(import.meta.url));
const ROOT = dirname(DIR);
const PORT = process.env.PORT || 4321;
const TYPES = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".mjs": "text/javascript" };
const AGENTS = ["memory-echo", "showrunner", "git-committer", "open-translate", "skippy-concierge"];
const PYTHON = existsSync(join(ROOT, ".venv", "bin", "python")) ? join(ROOT, ".venv", "bin", "python") : "python3";

function readBody(req, limit = 120_000) {
  return new Promise((resolve, reject) => {
    let body = "";
    req.on("data", chunk => {
      body += chunk.toString();
      if (body.length > limit) {
        reject(new Error("request body too large"));
        req.destroy();
      }
    });
    req.on("end", () => resolve(body));
    req.on("error", reject);
  });
}

function jsonResponse(res, status, payload) {
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(JSON.stringify(payload));
}

function runGitCommitter(diff) {
  return new Promise((resolve) => {
    const child = spawn(
      PYTHON,
      [join(ROOT, "agents", "git-committer", "review.py"), "--format", "text"],
      { cwd: ROOT, env: process.env, stdio: ["pipe", "pipe", "pipe"] }
    );
    let stdout = "";
    let stderr = "";
    const timer = setTimeout(() => {
      child.kill("SIGTERM");
      resolve({ ok: false, output: "git-committer timed out after 60 seconds." });
    }, 60_000);
    child.stdout.on("data", chunk => { stdout += chunk.toString(); });
    child.stderr.on("data", chunk => { stderr += chunk.toString(); });
    child.on("close", code => {
      clearTimeout(timer);
      resolve({
        ok: code === 0,
        output: (stdout || stderr || `git-committer exited with code ${code}`).trim(),
      });
    });
    child.stdin.end(diff);
  });
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  if (req.method === "POST" && url.pathname.startsWith("/api/")) {
    const agent = url.pathname.slice(5);
    if (agent === "git-committer") {
      try {
        const body = await readBody(req);
        const data = JSON.parse(body || "{}");
        const diff = String(data.input || data.diff || "").trim();
        if (!diff) {
          jsonResponse(res, 400, { ok: false, output: "Paste a unified diff before running review." });
          return;
        }
        const result = await runGitCommitter(diff);
        jsonResponse(res, result.ok ? 200 : 500, result);
      } catch (err) {
        jsonResponse(res, 400, { ok: false, output: err.message });
      }
      return;
    }
    if (AGENTS.includes(agent)) {
      res.writeHead(501, { "Content-Type": "application/json" });
      res.end(JSON.stringify({
        ok: false,
        output: `${agent} backend not wired yet — connect this endpoint to the agent's runner.`
      }));
      return;
    } else {
      res.writeHead(404, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ ok: false, output: "unknown agent" }));
      return;
    }
  }

  let path = decodeURIComponent(url.pathname);
  if (path === "/") path = "/index.html";
  const file = join(DIR, normalize(path).replace(/^(\.\.[/\\])+/, ""));
  if (!file.startsWith(DIR)) { res.writeHead(403).end("forbidden"); return; }
  try {
    const body = await readFile(file);
    const ext = file.slice(file.lastIndexOf("."));
    res.writeHead(200, { "Content-Type": TYPES[ext] || "application/octet-stream" });
    res.end(body);
  } catch {
    res.writeHead(404, { "Content-Type": "text/html" });
    res.end("<p>404 — not found. Did you run <code>node webui/build.mjs</code>?</p>");
  }
});

server.listen(PORT, () => console.log(`agent WebUIs on http://localhost:${PORT}`));
