"""Blogger: draft the build-journey blog post from the repo's own activity.

Reads HACKATHON.md (the per-track log) + recent git commits, then has qwen-plus
write ONE cohesive narrative post. The journey writes itself as we go — and it
dogfoods the same Qwen spine the five agents call at runtime.

    python docs/submission-kit/blogger.py            # writes blog-draft.md
    python docs/submission-kit/blogger.py --check     # offline self-check, no API

ponytail: no template engine, no per-section orchestration, no "last run" state.
The output is a *draft* we hand-polish. Add --since for incremental posts later.
"""

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent  # repo root: docs/submission-kit/ -> ../../
sys.path.insert(0, str(ROOT / "shared"))  # match smoke_test.py's bare import

SYSTEM = """You are documenting a hackathon build for a blog-post award.
Write ONE cohesive narrative blog post in Markdown from the activity log and
commit history below. Arc: hook -> what we built -> the hard bits -> what's next.

GROUNDING (hard rules — a judge will check against the repo):
- Use ONLY facts present in the inputs below. Do NOT invent commit hashes, dates,
  file names, technologies, agent behaviours, metrics, or events.
- If the log is thin, write a SHORT honest post about the actual current stage.
  Padding a sparse repo into a fake epic is the one thing that loses this award.
- When unsure, say less. Specific-but-true beats detailed-but-invented.

Context (true): five Qwen agents will share one memory brain and call Qwen Cloud
at runtime. No marketing fluff."""


def build_prompt(log: str, commits: str) -> str:
    """Assemble the full prompt. Pure string work — the testable core."""
    return (
        f"{SYSTEM}\n\n"
        f"## HACKATHON.md (per-track log)\n{log}\n\n"
        f"## Recent commits\n{commits}\n"
    )


def gather(commits: int) -> tuple[str, str]:
    """Read the two activity sources from the repo."""
    log = (ROOT / "HACKATHON.md").read_text()
    commits_out = subprocess.run(
        ["git", "-C", str(ROOT), "log", f"-n{commits}", "--pretty=format:%ad %s", "--date=short"],
        capture_output=True, text=True, check=True,
    ).stdout
    return log, commits_out


def generate(commits: int, out: Path) -> Path:
    from dashscope import chat  # imported here so --check stays offline

    log, commits_out = gather(commits)
    post = chat(build_prompt(log, commits_out))
    out.write_text(post)
    return out


def check() -> None:
    """Self-check: inputs load and the prompt assembles with both sources. No API."""
    log, commits_out = gather(10)
    prompt = build_prompt(log, commits_out)
    assert "HACKATHON.md" in prompt and log.strip() in prompt, "log missing from prompt"
    assert commits_out.strip() and commits_out.strip() in prompt, "commits missing from prompt"
    assert len(prompt) > len(SYSTEM), "prompt did not grow past the system text"
    print("OK: inputs load, prompt assembles with both sources.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commits", type=int, default=30, help="how many recent commits to feed in")
    ap.add_argument("--out", type=Path, default=HERE / "blog-draft.md", help="where to write the draft")
    ap.add_argument("--check", action="store_true", help="offline self-check, no API call")
    args = ap.parse_args()

    if args.check:
        check()
        return
    path = generate(args.commits, args.out)
    print(f"draft -> {path}")


if __name__ == "__main__":
    main()
