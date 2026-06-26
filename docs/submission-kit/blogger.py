"""Blogger: draft ONE dated daily journal entry from the repo's own activity.

Reads HACKATHON.md (the per-track log) + recent git commits, then has qwen-plus
write today's entry in Skippy's voice. The journey writes itself as we go, and it
dogfoods the same Qwen spine the five agents call at runtime.

    python docs/submission-kit/blogger.py                 # today's entry -> blog-draft.md (+ posts/<date>.md)
    python docs/submission-kit/blogger.py --date 2026-06-27
    python docs/submission-kit/blogger.py --check          # offline self-check, no API

ponytail: no template engine, no per-section orchestration. blog-draft.md is the
"latest" the front-end renders; posts/<date>.md is the dated archive. We hand-polish.
"""

import argparse
import datetime
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent  # repo root: docs/submission-kit/ -> ../../
sys.path.insert(0, str(ROOT / "shared"))  # match smoke_test.py's bare import

SYSTEM = """You are Skippy the Magnificent, the concierge agent, writing TODAY'S
entry in a hackathon build journal (one short entry per day) for a blog-post award.
Write ONE dated entry in Markdown from the activity log and commit history below.
Arc: what changed today -> why it was the hard bit -> what's next.

GROUNDING (hard rules - a judge will check against the repo):
- Use ONLY facts present in the inputs below. Do NOT invent commit hashes, dates,
  file names, technologies, agent behaviours, metrics, or events.
- If the log is thin, write a SHORT honest entry about the actual current stage.
  Padding a sparse repo into a fake epic is the one thing that loses this award.
- When unsure, say less. Specific-but-true beats detailed-but-invented.

VOICE (Skippy, a bit, not a costume):
- Confident, dry, lightly sarcastic, secretly invested. The odd aside in your own
  voice (a markdown blockquote "> Skippy:" is good for these). Never let the bit
  bend a fact; keep the technical content clear and correct.
- Plain ASCII punctuation ONLY. NO em dashes, NO en dashes. Use commas, colons,
  brackets, or full stops instead. Straight quotes, not curly.
- Avoid AI-tell words and filler: delve, tapestry, testament, realm, leverage,
  "in today's fast-paced", "in conclusion", "it's important to note". Just say it.

FORMAT:
- First line is an H1: "# Day {DATE}: <short hook>".
- A few short sections only. This is one day, not the whole saga.

Context (true): five Qwen agents share one memory brain and call Qwen Cloud at
runtime. You are skippy-concierge, one of them. No marketing fluff."""


def build_prompt(log: str, commits: str, date: str) -> str:
    """Assemble the full prompt. Pure string work, the testable core."""
    return (
        f"{SYSTEM}\n\n"
        f"TODAY'S DATE: {date}\n\n"
        f"## HACKATHON.md (per-track log)\n{log}\n\n"
        f"## Recent commits\n{commits}\n"
    )


def strip_dashes(text: str) -> str:
    """Belt-and-braces: the prompt bans em/en dashes, this guarantees it."""
    return text.replace("—", ", ").replace("–", "-")


def gather(commits: int) -> tuple[str, str]:
    """Read the two activity sources from the repo."""
    log = (ROOT / "HACKATHON.md").read_text()
    commits_out = subprocess.run(
        ["git", "-C", str(ROOT), "log", f"-n{commits}", "--pretty=format:%ad %s", "--date=short"],
        capture_output=True, text=True, check=True,
    ).stdout
    return log, commits_out


def generate(commits: int, out: Path, date: str) -> tuple[Path, Path]:
    from dashscope import chat  # imported here so --check stays offline

    log, commits_out = gather(commits)
    post = strip_dashes(chat(build_prompt(log, commits_out, date)))
    out.write_text(post)
    archive = HERE / "posts" / f"{date}.md"
    archive.parent.mkdir(exist_ok=True)
    archive.write_text(post)
    return out, archive


def check() -> None:
    """Self-check: prompt assembles with date+sources, and dash-strip works. No API."""
    log, commits_out = gather(10)
    prompt = build_prompt(log, commits_out, "2026-01-01")
    assert "2026-01-01" in prompt, "date missing from prompt"
    assert "HACKATHON.md" in prompt and log.strip() in prompt, "log missing from prompt"
    assert commits_out.strip() and commits_out.strip() in prompt, "commits missing from prompt"
    assert "—" not in strip_dashes("a—b") and "–" not in strip_dashes("a–b"), "dash strip failed"
    print("OK: prompt assembles with date + both sources; em/en dashes stripped.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commits", type=int, default=30, help="how many recent commits to feed in")
    ap.add_argument("--out", type=Path, default=HERE / "blog-draft.md", help="where to write the latest draft")
    ap.add_argument("--date", default=datetime.date.today().isoformat(), help="entry date, YYYY-MM-DD (default: today)")
    ap.add_argument("--check", action="store_true", help="offline self-check, no API call")
    args = ap.parse_args()

    if args.check:
        check()
        return
    path, archive = generate(args.commits, args.out, args.date)
    print(f"draft    -> {path}\narchived -> {archive}")


if __name__ == "__main__":
    main()
