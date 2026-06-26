"""Post-task continuous-improvement checklist.

Run after a worker changes the repo. It inspects changed files and reports the
documentation, architecture, testing, changelog, convention, and follow-up issue
reviews that should happen before a PR is opened.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def changed_files() -> list[str]:
    commands = [
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "diff", "--name-only", "--cached"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    files: set[str] = set()
    for command in commands:
        out = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True).stdout
        files.update(line.strip() for line in out.splitlines() if line.strip())
    return sorted(files)


def build_report(files: list[str]) -> dict[str, object]:
    touched = set(files)
    code_changed = any(path.endswith((".py", ".mjs", ".js", ".sql", ".yaml", ".yml")) for path in files)
    shared_changed = any(path.startswith("shared/") for path in files)
    agent_changed = any(path.startswith("agents/") for path in files)
    brain_changed = any(path.startswith("brain/") for path in files)
    docs_changed = any(path.startswith("docs/") or path in {"README.md", "shared/README.md"} for path in files)

    checks = [
        check("tests", code_changed, "Run `make test`; add focused tests for changed shared/agent behavior."),
        check("readme", code_changed and not docs_changed, "Review README/shared docs for user-facing behavior changes."),
        check("architecture", shared_changed or brain_changed, "Update docs/architecture for shared spine, brain, or deployment changes."),
        check("agent_docs", agent_changed, "Update the affected agent README/PLAN with behavior and validation notes."),
        check("changelog", code_changed and "CHANGELOG.md" not in touched, "Add or update CHANGELOG.md before the first release cut."),
        check("conventions", code_changed, "Check whether new rules belong in shared.code-conventions memory."),
        check("future_issues", True, "Capture skipped tests, TODOs, and deferred work as PR notes or issues."),
    ]
    return {
        "changed_files": files,
        "checks": checks,
        "required": [item for item in checks if item["required"]],
    }


def check(name: str, required: bool, action: str) -> dict[str, object]:
    return {"name": name, "required": required, "action": action}


def main() -> int:
    report = build_report(changed_files())
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
