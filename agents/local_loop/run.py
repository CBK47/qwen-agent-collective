#!/usr/bin/env python3
"""
Local autonomous coding loop agent.
Called by n8n every 15 minutes. Does: review → propose edit → validate → commit.
All output goes to stdout so n8n can capture it.
"""
import json, subprocess, urllib.request, sys, os, re, datetime
from pathlib import Path

REPO = os.environ.get("REPO_PATH", str(Path(__file__).resolve().parents[2]))
OLLAMA = "http://172.20.0.1:11434/api/chat"
MODEL = os.environ.get("OLLAMA_CODE_MODEL", "qwen3-next-cbk:latest")

ALLOWED_EDIT_ROOTS = ("agents/", "shared/", "brain/demo/")
MAX_APPEND_CHARS = 1200

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

def extract_json_object(text):
    """Return the first JSON object from model output, including fenced JSON."""
    fences = re.findall(r'```(?:json)?\n?([\s\S]*?)```', text)
    candidates = fences + [text]
    for candidate in candidates:
        candidate = candidate.strip()
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            continue
        try:
            return json.loads(candidate[start:end + 1])
        except json.JSONDecodeError:
            continue
    return None


def validate_append_edit(payload):
    """Validate the model's narrow edit contract and return (path, content)."""
    if not isinstance(payload, dict):
        raise ValueError("model did not return a JSON object")

    rel_path = str(payload.get("path", "")).strip().lstrip("./")
    append_text = payload.get("append", "")

    if not rel_path.endswith(".py"):
        raise ValueError("only Python files can be edited by local-loop")
    if os.path.isabs(rel_path) or ".." in rel_path.split(os.sep):
        raise ValueError("edit path must stay inside the repository")
    if not rel_path.startswith(ALLOWED_EDIT_ROOTS):
        raise ValueError(f"edit path must start with one of {ALLOWED_EDIT_ROOTS}")
    if not isinstance(append_text, str) or not append_text.strip():
        raise ValueError("append content is empty")
    if len(append_text) > MAX_APPEND_CHARS:
        raise ValueError(f"append content exceeds {MAX_APPEND_CHARS} characters")

    abs_path = os.path.realpath(os.path.join(REPO, rel_path))
    repo_root = os.path.realpath(REPO) + os.sep
    if not abs_path.startswith(repo_root):
        raise ValueError("resolved edit path escaped the repository")
    if not os.path.exists(abs_path):
        raise ValueError("local-loop only edits existing files")

    return rel_path, append_text.rstrip() + "\n"


def extract_commit_msg(text):
    """Return first line matching Conventional Commits, else clean fallback."""
    cc = re.compile(r'^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(\w[\w-]*\))?!?:\s.{3,}', re.I)
    for line in text.split("\n"):
        line = line.strip().strip("\"'`")
        if cc.match(line):
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
     "You are an autonomous coding assistant. Output ONLY one JSON object.\n\n"
     "Schema:\n"
     "{\n"
     "  \"path\": \"existing relative .py path under agents/, shared/, or brain/demo/\",\n"
     "  \"append\": \"small Python comment/docstring/helper stub to append\",\n"
     "  \"description\": \"short summary\"\n"
     "}\n\n"
     "Rules:\n"
     "- Do not output shell, markdown, commands, or explanations.\n"
     "- Append only; do not ask to rewrite or delete files.\n"
     "- Keep append under 1200 characters.\n"
     "- Prefer harmless docs, comments, or TODO stubs."},
    {"role": "user", "content":
     f"Review:\n{review}\n\n"
     f"Target file ({target_file}):\n```python\n{file_content}\n```\n\n"
     "Return the JSON edit object now."}
], temperature=0.1, num_predict=6000)

payload = extract_json_object(code_raw)
edit_path = None
run_output = ""

# ── 5. Safety check ────────────────────────────────────────────────────────────
try:
    edit_path, append_text = validate_append_edit(payload)
    print(f"[5/7] Safety PASSED: append to {edit_path}")
except Exception as exc:
    print(f"[5/7] Edit rejected — using report-only commit: {exc}")
    edit_path = None

# ── 6. Apply edit directly ─────────────────────────────────────────────────────
if edit_path:
    print("[6/7] Applying validated append...")
    with open(os.path.join(REPO, edit_path), "a", encoding="utf-8") as f:
        f.write("\n" + append_text)
    run_output = payload.get("description", f"append validated note to {edit_path}") if isinstance(payload, dict) else ""
    print(f"Applied: {run_output[:200]}")
else:
    print("[6/7] Skipped (no-op)")

# ── 7. Commit everything (report + any code changes) ──────────────────────────
print("[7/7] Committing...")
paths_to_stage = [os.path.relpath(rpath, REPO)]
if edit_path:
    paths_to_stage.append(edit_path)
subprocess.run(["git", "add", "--", *paths_to_stage], cwd=REPO, check=True)
status = subprocess.check_output(["git", "diff", "--staged", "--stat"], cwd=REPO, text=True).strip()

if not status:
    print("Nothing to commit.")
    sys.exit(0)

print(f"Staged:\n{status}")

# Generate commit message
summary = run_output or review.split("\n")[2] if "\n" in review else "automated review"
msg_raw = ollama([
    {"role": "system", "content":
     "You are a commit message generator. Reply with ONE LINE ONLY.\n"
     "Format: <type>(<scope>): <description>\n"
     "Types: feat fix docs chore refactor test\n"
     "Example: feat(agents): add synthesize_reviews stub to debate_prototype\n"
     "Your entire response must be just that one line. No explanation, no quotes."},
    {"role": "user", "content": f"Work done: {summary[:200]}\nFiles changed:\n{status[:300]}"}
], temperature=0, num_predict=200)

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
