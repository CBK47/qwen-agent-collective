#!/usr/bin/env node
/**
 * Zero-dependency static server for the agent WebUIs.
 *   node webui/server.mjs           # serves on http://localhost:4321
 *   PORT=8080 node webui/server.mjs
 *
 * Also exposes a stub /api/<agent> so the demo consoles get a clear, friendly
 * "not wired yet" response until each agent's real backend is connected.
 */
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join, normalize } from "node:path";

const DIR = dirname(fileURLToPath(import.meta.url));
const PORT = process.env.PORT || 4321;
const TYPES = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".mjs": "text/javascript" };
const AGENTS = ["memory-echo", "showrunner", "git-committer", "open-translate", "skippy-concierge"];

const server = createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  if (req.method === "POST" && url.pathname.startsWith("/api/")) {
    const agent = url.pathname.slice(5);
    if (agent === 'memory-echo') {
      let body = '';
      req.on('data', chunk => {
        body += chunk.toString();
      });
      req.on('end', () => {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, output: body }));
      });
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
  if (path.startsWith('/git-committer')) {
    path = '/agents/git-committer' + path.slice('/git-committer'.length);
  }
  if (path === '/agents/git-committer') {
    path += '/index.html';
  }
  if (path.startsWith('/memory-echo')) {
    path = '/agents/memory-echo' + path.slice('/memory-echo'.length);
  }
  if (path === '/agents/memory-echo') {
    path += '/index.html';
  }
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
