#!/usr/bin/env node
/**
 * Local autonomous coding loop (Node.js — runs inside the n8n Docker container,
 * or directly on the host). Pipeline:
 *
 *   1. gather rich, planning-grade context (git state, recent commits,
 *      PLAN.md checklists, source inventory)
 *   2. PLAN  — model picks ONE high-value, concrete slice on a file that has
 *              NOT been touched recently, returning structured JSON
 *   3. report — the plan is written to reports/local-worker/<date>/
 *   4. CODE  — model returns the COMPLETE new file content (no shell heredoc),
 *              written directly to disk so it can make real edits, not just appends
 *   5. VERIFY — language-aware syntax check + anti-truncation + safety scan
 *   6. COMMIT — only when real (non-report) code changed, with a descriptive
 *               conventional-commit message derived from the plan
 *
 * Env:
 *   OLLAMA_URL          default http://172.20.0.1:11434  (host: http://localhost:11434)
 *   OLLAMA_CODE_MODEL   default qwen3-next-cbk:latest
 */
import { execSync, spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync, readFileSync, existsSync, statSync } from "node:fs";
import { join, dirname, extname, basename } from "node:path";
import { tmpdir } from "node:os";

const REPO = "/home/cbk/qwen-agent-collective";
const OLLAMA = (process.env.OLLAMA_URL || "http://172.20.0.1:11434").replace(/\/$/, "") + "/api/chat";
const MODEL = process.env.OLLAMA_CODE_MODEL || "qwen3-next-cbk:latest";

// Files / dirs the loop must never write to or commit-pollute.
// Full-file rewrite is safe only for small/medium files. Larger, mature files
// (e.g. the 19KB shared client) must not be wholesale-rewritten by a flaky local model.
const MAX_REWRITE = 7000; // bytes
const fileBytes = (f) => { try { return statSync(join(REPO, f)).size; } catch { return 0; } };

const PROTECTED = [
  "agents/local_loop/run.mjs", "agents/local_loop/run.py",
  ".env", ".git", "node_modules", "package-lock.json", "package.json",
  "yarn.lock", "pnpm-lock.yaml",
];
// Destructive / dangerous substrings rejected in generated file content.
const CONTENT_BLOCKED = [
  "rm -rf", "rm -fr", ":(){", "mkfs", "dd if=", "> /dev/sd",
  "shutil.rmtree('/')", "os.system('rm", "subprocess.call(['rm",
  "DROP DATABASE", "DROP TABLE", "--no-preserve-root",
];

const log = (...a) => console.log(...a);

// ── Ollama ──────────────────────────────────────────────────────────────────
async function ollama(messages, { temperature = 0.2, numPredict = 4000 } = {}) {
  const resp = await fetch(OLLAMA, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: MODEL, think: false, stream: false,
      options: { temperature, num_predict: numPredict },
      messages,
    }),
    signal: AbortSignal.timeout(240_000),
  });
  if (!resp.ok) throw new Error(`Ollama HTTP ${resp.status}`);
  const data = await resp.json();
  let raw = data?.message?.content || "";
  // Strip thinking: full <think>…</think> pairs, then any dangling prefix.
  raw = raw.replace(/<think>[\s\S]*?<\/think>/g, "");
  if (raw.includes("</think>")) raw = raw.split("</think>").pop();
  return raw.trim();
}

function sh(cmd, opts = {}) {
  return execSync(cmd, { cwd: REPO, encoding: "utf8", ...opts }).trim();
}
function shSafe(cmd) { try { return sh(cmd); } catch { return ""; } }

// ── 1. Context ──────────────────────────────────────────────────────────────
log("[1/6] Gathering planning-grade context...");

const recentCommits = shSafe("git log --oneline -12");
// Files touched in the last 8 commits — the planner must avoid these.
const recentlyTouched = new Set(
  shSafe("git diff HEAD~8 HEAD --name-only 2>/dev/null")
    .split("\n").map(s => s.trim()).filter(Boolean)
    .filter(f => !f.startsWith("reports/"))
);

// Source inventory (code + docs), excluding noise, with line counts.
const inventory = shSafe(
  "git ls-files '*.py' '*.mjs' '*.js' '*.md' " +
  "| grep -vE '(^|/)(node_modules|venv|__pycache__|reports)/' "
).split("\n").filter(Boolean);

const inventoryDigest = inventory.map(f => {
  const p = join(REPO, f);
  let lines = 0;
  try { lines = readFileSync(p, "utf8").split("\n").length; } catch {}
  const recent = recentlyTouched.has(f) ? "  [recently touched — AVOID]" : "";
  return `- ${f} (${lines} lines)${recent}`;
}).join("\n");

// Unchecked checklist items from every PLAN.md — concrete work to advance.
const planItems = inventory.filter(f => /PLAN\.md$/.test(f)).flatMap(f => {
  const body = shSafe(`cat ${JSON.stringify(join(REPO, f))}`);
  return body.split("\n")
    .filter(l => /^\s*- \[ \]/.test(l))
    .map(l => `(${f}) ${l.trim()}`);
}).slice(0, 25);

const ctx =
  `### Recent commits (do NOT repeat these targets) ###\n${recentCommits}\n\n` +
  `### Source inventory ###\n${inventoryDigest}\n\n` +
  `### Open PLAN.md checklist items (high-value work to advance) ###\n` +
  (planItems.length ? planItems.join("\n") : "(none)");

// ── 2. PLAN ─────────────────────────────────────────────────────────────────
log("[2/6] Planning next work slice...");

const planRaw = await ollama([
  { role: "system", content:
    "/no_think\n" +
    "You are the planning agent for the qwen-agent-collective repo — a multi-agent " +
    "system where each agent advances its PLAN.md.\n\n" +
    "Choose ONE concrete, genuinely valuable next slice of work. Prefer advancing an " +
    "open PLAN.md checklist item, fleshing out a stub into real logic, adding a " +
    "missing docstring/type hints to a real public function, or improving a README to " +
    "match the code. AVOID files marked '[recently touched]'. AVOID trivial no-ops.\n\n" +
    "IMPORTANT: keep any reasoning to 3 short sentences MAX, then immediately output a " +
    "line starting with `PLAN_JSON:` followed by a single JSON object (and nothing after it). " +
    "Do not deliberate at length — decide quickly and emit the marker:\n" +
    'PLAN_JSON: {"target":"<repo-relative path to ONE file>",' +
    '"action":"edit"|"create",' +
    '"type":"feat"|"fix"|"docs"|"refactor"|"test"|"chore",' +
    '"goal":"<imperative, specific, <=70 chars — becomes the commit subject>",' +
    '"details":"<2-4 sentences: exactly what to change and why it is valuable>"}' },
  { role: "user", content: ctx + "\n\nDecide quickly (<=3 sentences) and emit the PLAN_JSON: line." },
], { temperature: 0.2, numPredict: 8000 });

function parsePlan(fullText) {
  // Prefer JSON after the explicit PLAN_JSON: marker; fall back to scanning all text.
  const mk = fullText.lastIndexOf("PLAN_JSON:");
  const text = mk !== -1 ? fullText.slice(mk + "PLAN_JSON:".length) : fullText;
  // Scan for every balanced {...} block (thinking text may contain stray braces),
  // try to parse each, and prefer the last one that has a "target" field.
  const candidates = [];
  for (let i = 0; i < text.length; i++) {
    if (text[i] !== "{") continue;
    let depth = 0, inStr = false, esc = false;
    for (let j = i; j < text.length; j++) {
      const c = text[j];
      if (inStr) { if (esc) esc = false; else if (c === "\\") esc = true; else if (c === '"') inStr = false; continue; }
      if (c === '"') inStr = true;
      else if (c === "{") depth++;
      else if (c === "}") { depth--; if (depth === 0) { candidates.push(text.slice(i, j + 1)); break; } }
    }
  }
  let best = null;
  for (const raw of candidates) {
    for (const s of [raw, raw.replace(/,\s*([}\]])/g, "$1")]) {
      try { const o = JSON.parse(s); if (o && typeof o === "object") { if (o.target) return o; best = best || o; } } catch {}
    }
  }
  return best;
}

let plan = parsePlan(planRaw);
if (!plan || !plan.target) log(`Planner raw tail: ${JSON.stringify(planRaw.slice(-300))}`);
if (!plan || !plan.target || !plan.goal) {
  log("Planner output unusable — falling back to a rotation target.");
  const fallback = rotationPick();
  plan = { target: fallback, action: "edit", type: "docs",
    goal: "improve documentation and type clarity",
    details: "Planner produced no usable plan; performing a safe documentation pass." };
}

// Normalise + guard the target.
let target = String(plan.target).replace(/^\.?\//, "").trim();
const targetPath = join(REPO, target);
const isProtected = PROTECTED.some(p => target === p || target.startsWith(p + "/"));
const escapes = !targetPath.startsWith(REPO + "/");
const inNoise = /(^|\/)(node_modules|venv|__pycache__|\.git)\//.test(target) ||
  target.startsWith("reports/");
// Real secret env files (.env, .env.local, …) — but allow templates (.env.example/.sample/.template).
const tbase = basename(target);
const isEnvSecret = tbase.startsWith(".env") && !/\.(example|sample|template)$/.test(tbase);
// Anything git-ignored must never be a target (covers .env, secrets, build artifacts).
const isIgnored = spawnSync("git", ["check-ignore", "-q", target], { cwd: REPO }).status === 0;

function rotationPick() {
  const ok = f => !recentlyTouched.has(f) && !PROTECTED.some(p => f === p || f.startsWith(p + "/")) &&
    !f.startsWith(".github/") && fileBytes(f) <= MAX_REWRITE;
  return inventory.find(f => /\.py$/.test(f) && /^(agents|shared)\//.test(f) && ok(f)) ||
    inventory.find(f => /\.md$/.test(f) && /^agents\//.test(f) && ok(f)) ||
    inventory.find(f => /\.py$/.test(f) && ok(f)) ||
    "agents/git-committer/README.md";
}
if (isProtected || escapes || inNoise || isEnvSecret || isIgnored) {
  log(`Planner chose a protected/secret/ignored target (${target}); rotating to a safe file.`);
  target = rotationPick();
} else if (fileBytes(target) > MAX_REWRITE) {
  log(`Target ${target} is ${fileBytes(target)}B — too large for safe full-rewrite; rotating.`);
  target = rotationPick();
}
plan.target = target;
log(`Plan: ${plan.type}(${target}) — ${plan.goal}`);

// ── 3. Report ───────────────────────────────────────────────────────────────
log("[3/6] Writing plan report...");
const now = new Date();
const dateStr = now.toISOString().slice(0, 10);
const tsStr = now.toISOString().replace(/[:.]/g, "-").slice(0, 19) + "Z";
const rdir = join(REPO, "reports", "local-worker", dateStr);
mkdirSync(rdir, { recursive: true });
const reportPath = join(rdir, `${tsStr}.md`);
writeFileSync(reportPath,
  `<!-- local-loop-agent -->\n<!-- generated_at: ${now.toISOString()} -->\n\n` +
  `# Local Loop Plan\n\n` +
  `- **Target:** \`${plan.target}\`\n- **Action:** ${plan.action}\n` +
  `- **Type:** ${plan.type}\n- **Goal:** ${plan.goal}\n\n` +
  `## Rationale\n${plan.details || "(none)"}\n`);

// ── 4. CODE (full-file rewrite) ─────────────────────────────────────────────
log("[4/6] Generating new file content...");
const ext = extname(target);
const langHint = { ".py": "python", ".mjs": "javascript", ".js": "javascript",
  ".json": "json", ".md": "markdown" }[ext] || "";

let oldContent = "";
if (existsSync(targetPath) && statSync(targetPath).isFile()) {
  oldContent = readFileSync(targetPath, "utf8");
  plan.action = "edit"; // file exists — never let a stray "create" overwrite it blind
} else {
  plan.action = "create"; // file missing — it's genuinely new
}
const oldForPrompt = oldContent; // target is size-capped, so show the whole file

const codeRaw = await ollama([
  { role: "system", content:
    "/no_think\n" +
    "You are a senior engineer making a SINGLE, focused, correct change to one file.\n\n" +
    "Output the COMPLETE final contents of the file — every line it should contain " +
    "after your change, ready to save verbatim. Make a real, coherent change that " +
    "satisfies the goal; do not just append a stub or a TODO. Preserve all existing " +
    "working code, imports, and style unless the goal requires changing it. Keep the " +
    "change tightly scoped.\n\n" +
    "Wrap the file content between these exact markers on their own lines:\n" +
    "<<<FILE\n...full file content...\nFILE>>>\n" +
    "Output nothing else — no explanation, no extra fences." },
  { role: "user", content:
    `Goal: ${plan.goal}\nDetails: ${plan.details || ""}\n` +
    `Target file: ${target} (${plan.action})\n\n` +
    (plan.action === "edit"
      ? `Current contents:\n\`\`\`${langHint}\n${oldForPrompt}\n\`\`\`\n\n` +
        `Return the FULL updated file between the markers.`
      : `This is a NEW file. Return its FULL initial contents between the markers.`) },
], { temperature: 0.1, numPredict: 10000 });

function extractFile(text) {
  const m = text.match(/<<<FILE\s*\n([\s\S]*?)\nFILE>>>/);
  if (m) return m[1].replace(/\n$/, "");
  // fallback: a single fenced block
  const f = text.match(/```[\w]*\n([\s\S]*?)```/);
  if (f) return f[1].replace(/\n$/, "");
  return null;
}

let newContent = extractFile(codeRaw);
if (newContent != null && !newContent.endsWith("\n")) newContent += "\n";

// ── 5. VERIFY ───────────────────────────────────────────────────────────────
log("[5/6] Verifying...");
function reject(reason) { log(`REJECTED: ${reason}`); cleanReset(); process.exit(0); }
// Surgical cleanup: ONLY the target file the loop touched and the report it wrote.
// Never operates on the whole tree — must not destroy unrelated/human changes.
function cleanReset() {
  const tracked = spawnSync("git", ["ls-files", "--error-unmatch", target],
    { cwd: REPO, encoding: "utf8" }).status === 0;
  if (tracked) shSafe(`git checkout -- ${JSON.stringify(target)} 2>/dev/null`);
  else if (existsSync(targetPath)) shSafe(`rm -f ${JSON.stringify(targetPath)}`);
  if (reportPath && existsSync(reportPath)) shSafe(`rm -f ${JSON.stringify(reportPath)}`);
}

if (!newContent || newContent.trim().length < 10) reject("model produced no usable file content");

// safety scan
const badHit = CONTENT_BLOCKED.find(b => newContent.includes(b));
if (badHit) reject(`blocked content: ${badHit}`);

// anti-truncation / anti-gutting: editing an existing file must not collapse it.
// Applies whenever the file already had real content, regardless of claimed action.
if (oldContent.length > 200 &&
    newContent.length < Math.max(60, oldContent.length * 0.6)) {
  reject(`suspected gutting (old ${oldContent.length} → new ${newContent.length} bytes)`);
}
if (newContent.length > 60_000) reject("output unreasonably large");

// language-aware syntax check
function pyHeuristics(s) {
  if ((s.match(/"""/g) || []).length % 2 !== 0) return "unbalanced triple-quotes";
  for (const ch of ["()", "[]", "{}"]) {
    const o = (s.match(new RegExp("\\" + ch[0], "g")) || []).length;
    const c = (s.match(new RegExp("\\" + ch[1], "g")) || []).length;
    if (o !== c) return `unbalanced ${ch}`;
  }
  return null;
}
function checkSyntax(content) {
  const tmp = join(tmpdir(), `loopchk-${Date.now()}${ext || ".txt"}`);
  writeFileSync(tmp, content);
  if (ext === ".json") { try { JSON.parse(content); return null; } catch (e) { return `invalid JSON: ${e.message}`; } }
  if (ext === ".mjs" || ext === ".js") {
    const r = spawnSync("node", ["--check", tmp], { encoding: "utf8" });
    return r.status === 0 ? null : `node --check failed: ${(r.stderr || "").slice(0, 200)}`;
  }
  if (ext === ".py") {
    const hasPy = spawnSync("sh", ["-c", "command -v python3"], { encoding: "utf8" }).status === 0;
    if (hasPy) {
      const r = spawnSync("python3", ["-m", "py_compile", tmp], { encoding: "utf8" });
      return r.status === 0 ? null : `py_compile failed: ${(r.stderr || "").slice(0, 200)}`;
    }
    return pyHeuristics(content);
  }
  return null; // md/txt etc.
}
const syntaxErr = checkSyntax(newContent);
if (syntaxErr) reject(syntaxErr);
log("Verify PASSED");

// ── apply ───────────────────────────────────────────────────────────────────
mkdirSync(dirname(targetPath), { recursive: true });
writeFileSync(targetPath, newContent);

// ── 6. COMMIT (only if real code changed, not just the report) ──────────────
log("[6/6] Committing...");
// Stage ONLY our own two files — never `git add -A` (that would sweep up
// unrelated or human-authored changes in the working tree).
sh(`git add ${JSON.stringify(target)} ${JSON.stringify(reportPath)}`);
const codeChanges = shSafe(`git diff --staged --name-only -- ${JSON.stringify(target)}`);
if (!codeChanges.trim()) {
  log("No code change vs HEAD (model reproduced the file) — skipping commit.");
  cleanReset();
  shSafe(`git reset -q HEAD ${JSON.stringify(reportPath)} 2>/dev/null`);
  process.exit(0);
}
log(`Staged:\n${shSafe("git diff --staged --stat")}`);

const scope = basename(target).replace(/\.\w+$/, "");
const type = ["feat", "fix", "docs", "refactor", "test", "chore"].includes(plan.type) ? plan.type : "chore";
const subject = String(plan.goal).replace(/[`"\n]/g, "").trim().slice(0, 70);
const commitMsg = `${type}(${scope}): ${subject}`;
const body = (plan.details || "").replace(/`/g, "").trim().slice(0, 300);
log(`Commit: ${commitMsg}`);

const res = spawnSync("git", [
  "-c", "user.name=local-loop-agent", "-c", "user.email=n8n@local",
  "commit", "-m", commitMsg, "-m", `${body}\n\nCo-Authored-By: local-loop-agent <n8n@local>`,
], { cwd: REPO, encoding: "utf8" });
log((res.stdout || "").trim());
if (res.status !== 0) { console.error(`Commit failed: ${(res.stderr || "").trim()}`); process.exit(1); }
log("SUCCESS");
