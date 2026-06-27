"""Model council — poll a handful of Qwen models on the real codebase.

Builds a compact digest of the repo (source tree, open plan tasks, the keystone
source) and asks several chat-capable Qwen models, in parallel, for (1) a short
honest review and (2) the ONE specific thing each would want to work on next.
The collected opinions are a cheap, diverse prioritisation signal.

    python -m shared.model_council
    python -m shared.model_council --save   # also write a report under reports/

Only models that responded in the bench are used by default.
"""

from __future__ import annotations

import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from shared.dashscope import chat

ROOT = Path(__file__).resolve().parents[1]

# Chat-capable free-tier models confirmed working by shared.model_bench.
COUNCIL = ["qwen-plus", "qwen-turbo", "qwen-max", "qwen3-coder-plus"]


def _sh(cmd: str) -> str:
    try:
        return subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:
        return ""


def build_digest() -> str:
    """A compact snapshot of the repo for the council to react to."""
    tree = _sh("git ls-files 'shared/*.py' 'agents/*/*.py' | head -30")
    open_tasks = _sh("git ls-files '*PLAN*.md' | xargs grep -hE '^\\s*- \\[ \\]' 2>/dev/null | head -20")
    keystone = ""
    p = ROOT / "shared" / "brain.py"
    if p.exists():
        keystone = "\n".join(p.read_text().splitlines()[:40])
    return (
        "### Source files ###\n" + tree +
        "\n\n### Open plan tasks ###\n" + (open_tasks or "(none)") +
        "\n\n### Keystone shared/brain.py (head) ###\n" + keystone
    )


PROMPT = (
    "You are reviewing the `qwen-agent-collective` repo: five specialist Qwen agents "
    "(memory-echo, showrunner, git-committer, open-translate, skippy-concierge) over a "
    "shared brain (Postgres + Qdrant), for a hackathon with five tracks.\n\n"
    "{digest}\n\n"
    "Respond in EXACTLY this form, concise:\n"
    "REVIEW: <2 sentences, honest>\n"
    "NEXT: <ONE specific task you'd want to work on — name the file and what you'd do>"
)


def poll(model: str, digest: str) -> str:
    try:
        return chat(PROMPT.format(digest=digest), model=model).strip()
    except Exception as exc:  # noqa: BLE001
        return f"(failed: {str(exc).splitlines()[0][:100]})"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Poll Qwen models on the codebase")
    ap.add_argument("--save", action="store_true", help="write a report under reports/model-council/")
    args = ap.parse_args(argv)

    digest = build_digest()
    print(f"Polling {len(COUNCIL)} models on the current codebase...\n")
    results: list[tuple[str, str]] = []
    for model in COUNCIL:
        ans = poll(model, digest)
        results.append((model, ans))
        print(f"━━ {model} ━━\n{ans}\n")

    if args.save:
        now = datetime.now(timezone.utc)
        out = ROOT / "reports" / "model-council" / now.strftime("%Y-%m-%d")
        out.mkdir(parents=True, exist_ok=True)
        path = out / (now.strftime("%Y-%m-%dT%H-%M-%SZ") + ".md")
        body = f"# Model Council — {now.isoformat()}\n\n"
        for model, ans in results:
            body += f"## {model}\n\n{ans}\n\n"
        path.write_text(body)
        print(f"saved -> {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
