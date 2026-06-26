"""Repo Health & Daily Sync: The central heart-beat for the project.
Designed to be triggered by n8n nightly via 'Execute Command'.

This script aggregates repo state, triggers the daily blog draft, 
and reports health status back to the orchestrator.
"""

import subprocess
import datetime
from pathlib import Path
import sys

# Setup paths relative to this file (shared/repo_health.py)
here = Path(__file__).resolve().parent
root = here.parent

def run_cmd(args: list[str], cwd=None) -> str:
    """Helper to run shell commands and capture output."""
    res = subprocess.run(
        args, 
        capture_output=True, 
        text=True, 
        cwd=cwd or str(root),
        check=False # We want to handle failures manually to report them in health check
    )
    return res.stdout.strip()

def get_git_status():
    """Check for uncommitted changes."""
    status = run_cmd(["git", "status", "--short"])
    return "Clean" if not status else f"Uncommitted changes:\n{status}"

def get_daily_log():
    """Get summary of work done since midnight."""
    # Format: hash | date | subject
    log = run_cmd(["git", "log", "--since=midnight", "--pretty=format:%h | %ad | %s", "--date=short"])
    return log if log else "No commits today."

def trigger_blogger():
    """Trigger the blogger.py to ensure a draft is ready for tomorrow."""
    today = datetime.date.today().isoformat()
    # We call the logger using absolute path to avoid PYTHONPATH issues in n8n
    cmd = [sys.executable, str(root / "docs/submission-kit/blogger.py"), "--date", today]
    out = run_cmd(cmd)
    
    # Verify if a file was actually written to the archive (based on blogger.py logic)
    blog_file = root / "docs/submission-kit/posts" / f"{today}.md"
    if blog_file.exists():
        return True, out
    return False, out

def main():
    print("--- 🌙 NIGHTLY REPO HEALTH REPORT ---")
    print(f"Date: {datetime.date.today().isoformat()}\n")

    # 1. Git Health
    status = get_git_status()
    print(f"[GIT STATUS]\n{status}\n")

    # 2. Productivity Log
    log = get_daily_log()
    print(f"[DAILY PROGRESS]\n{log}\n")

    # 3. Blog Synchronization
    success, msg = trigger_blogger()
    if success:
        print(f"[BLOG POST] ✅ Success: Today's journal entry generated.\n{msg}")
    else:
        print(f"[BLOG POST] ❌ Failed: No entry created for today. Please check blogger.py logs.")

    # Final Verdict for n8n
    if "❌" in (status + log + msg) or not success:
        print("\nVERDICT: WARNING - Repo health requires attention.")
        sys.exit(1) # Non-zero exit triggers error flow in n8n
    else:
        print("\nVERDICT: HEALTHY")
        sys.exit(0)

if __name__ == "__main__":
    main()
