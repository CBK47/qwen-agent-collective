#!/usr/bin/env node
/**
 * Local autonomous coding loop agent (Node.js — runs inside n8n Docker container).
 * Called by n8n every 15 minutes. Does: review → code → safety → run → commit.
 */
import { execSync, spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const REPO = "/home/cbk/qwen-agent-collective";
const OLLAMA = "http://172.20.0.1:11434/api/chat";
const MODEL = process.env.OLLAMA_CODE_MODEL || "qwen3-next-cbk:latest";

const BLOCKED = [
  "rm -rf", "rm -r", " rm ", "git push", "git reset --hard",
  "git commit", "apt-get", "pip install", "> /etc/", "> /usr/",
  "> /bin/", ":(){", "mkfs", "/dev/", "eval $(", "chmod 777",
];

async function ollama(messages, temperature = 0.2, numPredict = 4000) {
  const body = JSON.stringify({
    model: MODEL, think: false, stream: false,
    options: { temperature, num_predict: numPredict },
    messages,
  });
  const resp = await fetch(OLLAMA, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
    signal: AbortSignal.timeout(180_000),
  });
  const data = await resp.json();
  let raw = data?.message?.content || "";
  if (raw.includes("</think>")) raw = raw.split("</think>").pop();
  return raw.trim();
}

function extractScript(text) {
  const fences = [...text.matchAll(/```(?:sh|bash|shell)?\n?([\s\S]*?)```/g)];
  if (fences.length) return fences[fences.length - 1][1].trim();
  const idx = text.lastIndexOf("#!/");
  if (idx !== -1) return text.slice(idx).trim();
  return "";
}

function extractCommitMsg(text) {
  const cc = /^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(\w[\w-]*\))?!?:\s.{3,}/i;
  for (const line of text.split("\n")) {
    const l = line.trim().replace(/^[`"']+|[`"']+$/g, "");
    if (cc.test(l)) return l.slice(0, 72);
  }
  return "chore: automated improvement by local-loop";
}

function sh(cmd, opts = {}) {
  return execSync(cmd, { cwd: REPO, encoding: "utf8", ...opts }).trim();
}

// ── 1. Gather context ──────────────────────────────────────────────────────────
console.log("[1/7] Gathering repo context...");
const ctx = sh(
  "git status --short --branch && echo '### Recent commits ###' && git log --oneline -10 && " +
  "echo '### Files changed in last 5 commits ###' && git diff HEAD~5 HEAD --name-only 2>/dev/null | sort -u && " +
  "find . -name '*.py' ! -path './venv/*' ! -path './.git/*' | sort | head -6 | " +
  "xargs -I{} sh -c 'printf \"### %s ###\\n\" \"{}\" && head -30 \"{}\"'"
).slice(0, 4000);

// ── 2. Review ──────────────────────────────────────────────────────────────────
console.log("[2/7] Calling review model...");
const reviewRaw = await ollama([
  { role: "system", content:
    "You are a review agent for qwen-agent-collective.\n\n" +
    "Return EXACTLY this Markdown:\n" +
    "# Local Loop Report\n" +
    "## Verdict\n" +
    "PASS/WARN/FAIL + one sentence.\n" +
    "## Recommended Next Work Slice\n" +
    "ONE micro-task under 20 shell lines. Add a docstring, type hint, " +
    "TODO comment, or stub function. IMPORTANT: look at the recent commits list " +
    "and pick a FILE that has NOT been recently touched. Never recommend debate_prototype.py " +
    "if it already appears in the recent commits. Vary the target file each cycle." },
  { role: "user", content: `Repo context:\n\n${ctx}` },
], 0.2, 4000);

const hIdx = reviewRaw.search(/(?:^|\n)# /);
let review = hIdx !== -1
  ? reviewRaw.slice(reviewRaw[hIdx] === "\n" ? hIdx + 1 : hIdx).trim()
  : reviewRaw.trim();
if (!review.startsWith("#")) {
  review = "# Local Loop Report\n## Verdict\nWARN: model output unclear.\n## Recommended Next Work Slice\nAdd a docstring to the `run_debate` function in agents/git-committer/debate_prototype.py.";
}
const verdictLine = review.split("\n").find(l => /^(PASS|WARN|FAIL)/.test(l.trim())) || "?";
console.log(`Review verdict: ${verdictLine.trim()}`);

// ── 3. Write report ────────────────────────────────────────────────────────────
console.log("[3/7] Writing report...");
const now = new Date();
const dateStr = now.toISOString().slice(0, 10);
const tsStr = now.toISOString().replace(/[:.]/g, "-").slice(0, 19) + "Z";
const rdir = join(REPO, "reports", "local-worker", dateStr);
mkdirSync(rdir, { recursive: true });
const rpath = join(rdir, `${tsStr}.md`);
writeFileSync(rpath, `<!-- local-loop-agent -->\n<!-- generated_at: ${now.toISOString()} -->\n\n${review}\n`);

// ── 4. Call coder ──────────────────────────────────────────────────────────────
console.log("[4/7] Calling coding model...");
const fileMatch = review.match(/(?:in|edit|update|to)\s+([\w./]+\.py)/i);
const targetFile = fileMatch ? fileMatch[1].replace(/^\.\//, "") : "agents/git-committer/debate_prototype.py";
const targetPath = join(REPO, targetFile);
let fileContent = "";
if (existsSync(targetPath)) {
  fileContent = readFileSync(targetPath, "utf8").slice(0, 3000);
}

const codeRaw = await ollama([
  { role: "system", content:
    "You are an autonomous coding agent. Output a POSIX sh script.\n\n" +
    "RULES:\n" +
    "- First line MUST be: #!/bin/sh\n" +
    "- Use ONLY: echo, printf, cat, tee, mkdir -p\n" +
    "- Write/append to files with heredoc: cat >> path << 'HEREDOC' ... HEREDOC\n" +
    "- ALL paths relative to /home/cbk/qwen-agent-collective\n" +
    "- FORBIDDEN: rm, git push, git reset, git commit, pip install, apt-get, curl, wget\n" +
    "- Under 30 lines total\n" +
    "- Last line: echo 'DONE: <description>'\n" +
    "- Output ONLY the script. NO markdown fences. NO explanation. Start with #!/bin/sh" },
  { role: "user", content:
    `Review:\n${review}\n\nTarget file (${targetFile}):\n\`\`\`python\n${fileContent}\n\`\`\`\n\nWrite the sh script. Start immediately with #!/bin/sh on the first line.` },
], 0.1, 6000);

let script = extractScript(codeRaw);
// Last resort: find first #!/ line directly
if (!script) {
  const lines = codeRaw.split("\n");
  const si = lines.findIndex(l => l.startsWith("#!/"));
  if (si !== -1) script = lines.slice(si).join("\n").trim();
}
console.log(`Script extracted: ${script.length} chars, starts with: ${JSON.stringify(script.slice(0, 40))}`);

// ── 5. Safety ──────────────────────────────────────────────────────────────────
let safeScript = null;
if (!script || !script.startsWith("#!/")) {
  console.log("[5/7] No valid script — skipping");
} else {
  const hit = BLOCKED.find(b => script.includes(b));
  if (hit) {
    console.log(`[5/7] BLOCKED: ${hit}`);
  } else if (script.includes("/home/") && !script.includes("/home/cbk/qwen-agent-collective")) {
    console.log("[5/7] BLOCKED: path outside repo");
  } else {
    console.log("[5/7] Safety PASSED");
    safeScript = script;
  }
}

// ── 6. Run script ──────────────────────────────────────────────────────────────
let runOutput = "";
if (safeScript) {
  console.log("[6/7] Running script...");
  const run = spawnSync("sh", ["-c", safeScript], { cwd: REPO, encoding: "utf8", timeout: 60_000 });
  runOutput = (run.stdout || "").trim();
  console.log(`Exit: ${run.status}, output: ${runOutput.slice(0, 200)}`);
  if (run.stderr) console.log(`Stderr: ${run.stderr.slice(0, 200)}`);
} else {
  console.log("[6/7] Skipped (no safe script)");
}

// ── 7. Commit (only when real code changed, not just reports) ──────────────────
console.log("[7/7] Committing...");
sh("git add -A");
// Only count changes outside reports/ — skip report-only cycles
const codeChanges = sh("git diff --staged --name-only | grep -v '^reports/' || true");
if (!codeChanges.trim()) {
  console.log("No code changes this cycle — skipping commit (reports not committed alone).");
  sh("git reset HEAD -- .");
  process.exit(0);
}
const staged = sh("git diff --staged --stat");
console.log(`Staged:\n${staged}`);

const summary = runOutput || verdictLine;
const msgRaw = await ollama([
  { role: "system", content:
    "You are a commit message generator. Reply with ONE LINE ONLY.\n" +
    "Format: <type>(<scope>): <description>\n" +
    "Types: feat fix docs chore refactor test\n" +
    "Example: chore(agents): add synthesize_reviews stub to debate_prototype\n" +
    "Your entire response must be just that one line. No explanation, no quotes." },
  { role: "user", content: `Work done: ${summary.slice(0, 200)}\nFiles changed:\n${staged.slice(0, 300)}` },
], 0, 200);

const commitMsg = extractCommitMsg(msgRaw);
console.log(`Commit message: ${JSON.stringify(commitMsg)}`);

const commitResult = spawnSync(
  "git", [
    "-c", "user.name=local-loop-agent",
    "-c", "user.email=n8n@local",
    "commit", "-m", `${commitMsg}\n\nCo-Authored-By: local-loop-agent <n8n@local>`,
  ],
  { cwd: REPO, encoding: "utf8" }
);
console.log(commitResult.stdout.trim());
if (commitResult.status !== 0) {
  console.error(`Commit failed: ${commitResult.stderr.trim()}`);
  process.exit(1);
}
console.log("SUCCESS");
