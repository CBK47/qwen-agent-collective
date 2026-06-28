"""Importable façade for the project's shared code conventions.

The canonical definitions live in ``shared/code-conventions.py`` (dashed name,
kept for historical reasons). A dashed filename is **not** importable as a Python
module, so callers that wrote ``from shared.code_conventions import ...`` were
failing. This module is the importable home: it re-exports ``CONVENTIONS`` from
the dashed file (single source of truth) and adds a lightweight ``review_diff``
static check used by the demo/review tooling.

Usage:
    from shared.code_conventions import CONVENTIONS, review_diff
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Any

# ── re-export CONVENTIONS from the dashed canonical file ──────────────────────
_CANON = Path(__file__).with_name("code-conventions.py")
_spec = importlib.util.spec_from_file_location("_shared_code_conventions_canon", _CANON)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

CONVENTIONS: dict[str, Any] = _mod.CONVENTIONS


# ── lightweight diff review ───────────────────────────────────────────────────
def _added_lines(diff: str) -> list[tuple[int, str]]:
    """Return (1-based added-line index, text) for ``+`` lines in a unified diff.

    Plain (non-diff) input is treated as if every line were added, so the same
    checker works on a bare code snippet too.
    """
    if not any(line.startswith(("+++", "@@", "diff --git")) for line in diff.splitlines()):
        return list(enumerate(diff.splitlines(), start=1))
    out: list[tuple[int, str]] = []
    for i, line in enumerate(diff.splitlines(), start=1):
        if line.startswith("+") and not line.startswith("+++"):
            out.append((i, line[1:]))
    return out


def review_diff(diff: str) -> dict[str, Any]:
    """Statically check a diff/snippet against :data:`CONVENTIONS`.

    Args:
        diff: A unified diff or a raw code snippet.

    Returns:
        dict with ``ok`` (bool) and ``findings`` (list of
        ``{"line", "rule", "message"}``). Dependency-free and deterministic, so
        it is safe to call from demos, tests, and the git-committer pipeline.
    """
    max_len = CONVENTIONS["style"]["max_line_length"]
    findings: list[dict[str, Any]] = []

    for lineno, text in _added_lines(diff):
        if len(text) > max_len:
            findings.append({
                "line": lineno,
                "rule": "max_line_length",
                "message": f"line exceeds {max_len} chars ({len(text)})",
            })
        if "\t" in text:
            findings.append({
                "line": lineno,
                "rule": "indentation",
                "message": "tab character; use 4 spaces",
            })
        if re.search(r"except\s*:", text):
            findings.append({
                "line": lineno,
                "rule": "error_handling",
                "message": "bare except; catch a specific exception",
            })

    return {"ok": not findings, "findings": findings}


if __name__ == "__main__":
    sample = "+def add(a, b):\n+    return a - b\n+    x=1\n+    except:\n"
    print(review_diff(sample))
