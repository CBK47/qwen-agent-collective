#!/usr/bin/env python3
"""
Local autonomous coding loop agent.
Called by n8n every 15 minutes. Does: review → code → safety → run → commit.
All output goes to stdout so n8n can capture it.
"""
import json, subprocess, urllib.request, sys, os, re, datetime

REPO = "/home/cbk/qwen-agent-collective"
OLLAMA = "http://172.20.0.1:11434/api/chat"
MODEL = os.environ.get("OLLAMA_CODE_MODEL", "qwen3-next-cbk:latest")

BLOCKED_PATTERNS = [
    "rm -rf", "rm -r", " rm ", "git push", "git reset --hard",
    "git commit", "apt-get", "pip install", "> /etc/", "> /usr/",
    "> /bin/", ":(){", "mkfs", "/dev/", "eval $(", "chmod 777",
]

def ollama(messages, temperature=0.2, num_predict=4000):
    payload = {
        "model": MODEL, "think": False, "stream": False,
        "options": {"temperature": temperature, "num_predict": num_predict},
        "messages": messages,
    }
    req = urllib.request.Request(
        OLLAMA, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        raw = json.load(r).get("message", {}).get("content", "")
    # Strip <think> blocks if present
    if "</think>" in raw:
        raw = raw.split("</think>")[-1]
    return raw.strip()

def extract_script(text):
    """Find the last code fence or shebang block in text."""
    fences = re.findall(r'```(?:sh|bash|shell)?\n?([\s\S]*?)```', text)
    if fences:
        return fences[-1].strip()
    idx = text.rfind("#!/")
    if idx != -1:
        return text[idx:].strip()
    return ""

def extract_commit_msg(text):
    """Return first line matching Conventional Commits, else clean fallback."""
    cc = re.compile(r'^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(\w[\w-]*\))?!?:\s.{3,}', re.I)
    for line in text.split("\n"):
        line = line.strip().strip("\"'")
        if cc.match(line):
            return line[:72]
    # first non-thinking line
    bad_starts = ("okay", "let's", "i need", "the user", "here's", "first,",
                  "so,", "alright", "sure,", "well,", "now,", "conventional",
                  "the commit", "a commit", "looking", "based on")
    for line in text.split("\n"):
        line = line.strip().strip("\"'")
        if line and not any(line.lower().startswith(b) for b in bad_starts):
            return line[:72]
    return "chore: automated improvement by local-loop"

# ── 1. Gather context ──────────────────────────────────────────────────────────
print("[1/7] Gathering repo context...")
ctx = subprocess.check_output(
    ["bash", "-c",
     "git status --short --branch && git log --oneline -6 && "
     "find . -name '*.py' ! -path './venv/*' ! -path './.git/*' | sort | head -6 | "
     "xargs -I{} sh -c 'printf \"### %s ###\\n\" \"{}\" && head -30 \"{}\"'"],
    cwd=REPO, text=True
)[:4000]

# ── 2. Review ──────────────────────────────────────────────────────────────────
print("[2/7] Calling review model...")
review_raw = ollama([
    {"role": "system", "content":
     "You are a review agent for qwen-agent-collective.\n\n"
     "Return EXACTLY this Markdown:\n"
     "# Local Loop Report\n"
     "## Verdict\n"
     "PASS/WARN/FAIL + one sentence.\n"
     "## Recommended Next Work Slice\n"
     "ONE micro-task under 20 shell lines. Must be: add a docstring, type hint, "
     "TODO comment, stub function, or one-line addition to an existing tracked file. "
     "Name the EXACT file and function. NEVER recommend complex features, rewrites, "
     "or editing JSON/config files."},
    {"role": "user", "content": f"Repo context:\n\n{ctx}"}
], temperature=0.2, num_predict=4000)

# Anchor on first markdown heading
m = re.search(r'(?:^|\n)(#\s)', review_raw)
review = review_raw[m.start() if review_raw[m.start()] == '#' else m.start()+1:].strip() if m else review_raw.strip()
if not review.startswith("#"):
    review = "# Local Loop Report\n## Verdict\nWARN: model output unclear.\n## Recommended Next Work Slice\nAdd a docstring to the `run_debate` function in agents/git-committer/debate_prototype.py explaining its purpose."

print(f"Review verdict: {review.split(chr(10))[2] if len(review.split(chr(10))) > 2 else '?'}")

# ── 3. Write report ────────────────────────────────────────────────────────────
print("[3/7] Writing report...")
now = datetime.datetime.now(datetime.timezone.utc)
rdir = os.path.join(REPO, "reports", "local-worker", now.strftime("%Y-%m-%d"))
os.makedirs(rdir, exist_ok=True)
ts = now.strftime("%Y-%m-%dT%H-%M-%S") + "Z"
rpath = os.path.join(rdir, f"{ts}.md")
with open(rpath, "w") as f:
    f.write(f"<!-- local-loop-agent -->\n<!-- generated_at: {now.isoformat()} -->\n\n{review}\n")

# ── 4. Read target file ────────────────────────────────────────────────────────
print("[4/7] Calling coding model...")
# Extract file name from review
file_match = re.search(r'(?:in|edit|update|to)\s+([\w./]+\.py)', review, re.I)
target_file = file_match.group(1).lstrip("./") if file_match else "agents/git-committer/debate_prototype.py"
target_path = os.path.join(REPO, target_file)
file_content = ""
if os.path.exists(target_path):
    with open(target_path) as f:
        file_content = f.read()[:3000]

code_raw = ollama([
    {"role": "system", "content":
     "You are an autonomous coding agent. Output a POSIX sh script.\n\n"
     "RULES:\n"
     "- First line MUST be: #!/bin/sh\n"
     "- Use ONLY: echo, printf, cat, tee, mkdir -p\n"
     "- Write/append to files with heredoc: cat >> path << 'HEREDOC' ... HEREDOC\n"
     "- ALL paths relative to /home/cbk/qwen-agent-collective\n"
     "- FORBIDDEN: rm, git push, git reset, git commit, pip install, apt-get, curl, wget\n"
     "- Under 30 lines total\n"
     "- Last line: echo 'DONE: <description>'\n"
     "- Output ONLY the script. NO markdown fences. NO explanation. Start with #!/bin/sh"},
    {"role": "user", "content":
     f"Review:\n{review}\n\n"
     f"Target file ({target_file}):\n```python\n{file_content}\n```\n\n"
     "Write the sh script. Start immediately with #!/bin/sh on the first line."}
], temperature=0.1, num_predict=6000)

script = extract_script(code_raw)
if not script:
    # Last resort: if model output starts with #!/ after stripping leading text
    lines = code_raw.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("#!/"):
            script = "\n".join(lines[i:]).strip()
            break

print(f"Script extracted: {len(script)} chars, starts with: {script[:40]!r}")

# ── 5. Safety check ────────────────────────────────────────────────────────────
if not script or not script.startswith("#!/"):
    print("[5/7] No valid script — using no-op")
    script = None
else:
    hits = [b for b in BLOCKED_PATTERNS if b in script]
    if hits:
        print(f"[5/7] BLOCKED: {hits}")
        script = None
    elif "/home/" in script and "/home/cbk/qwen-agent-collective" not in script:
        print("[5/7] BLOCKED: path outside repo")
        script = None
    else:
        print("[5/7] Safety PASSED")

# ── 6. Run script ──────────────────────────────────────────────────────────────
run_output = ""
if script:
    print("[6/7] Running script...")
    run = subprocess.run(["sh", "-c", script], cwd=REPO, capture_output=True, text=True, timeout=60)
    run_output = run.stdout.strip()
    print(f"Exit: {run.returncode}, output: {run_output[:200]}")
    if run.stderr:
        print(f"Stderr: {run.stderr[:200]}")
else:
    print("[6/7] Skipped (no-op)")

# ── 7. Commit everything (report + any code changes) ──────────────────────────
print("[7/7] Committing...")
subprocess.run(["git", "add", "-A"], cwd=REPO, check=True)  # -A includes new files
status = subprocess.check_output(["git", "diff", "--staged", "--stat"], cwd=REPO, text=True).strip()

if not status:
    print("Nothing to commit.")
    sys.exit(0)

print(f"Staged:\n{status}")

# Generate commit message
summary = run_output or review.split("\n")[2] if "\n" in review else "automated review"
msg_raw = ollama([
    {"role": "system", "content":
     "Output ONLY a git commit message. Single line, max 60 chars, "
     "Conventional Commits (feat/fix/docs/chore/refactor: description). "
     "Start directly with the type. Nothing else."},
    {"role": "user", "content": f"Work done: {summary[:200]}\nFiles changed:\n{status[:300]}"}
], temperature=0, num_predict=1000)

commit_msg = extract_commit_msg(msg_raw)
print(f"Commit message: {commit_msg!r}")

r = subprocess.run(
    ["git", "commit", "-m", f"{commit_msg}\n\nCo-Authored-By: local-loop-agent <n8n@local>"],
    cwd=REPO, capture_output=True, text=True
)
print(r.stdout.strip())
if r.returncode != 0:
    print(f"Commit failed: {r.stderr.strip()}")
    sys.exit(1)

print("SUCCESS")
