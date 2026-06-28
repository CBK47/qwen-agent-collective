"""GIT-Committer · Multi-Agent PR Review CLI (Track 3 MVP).

Usage:
    python agents/git-committer/review.py --diff-file path/to/diff.patch
    git diff HEAD~1 | python agents/git-committer/review.py

Mirrors the logic in brain/orchestrator/workflows/git-committer-pr-review.json:
  3 role reviewers (correctness, security, style/test-coverage) run sequentially
  here (the n8n version fans them out in parallel via Promise.all), then a
  negotiation step merges findings into one verdict, and a single-agent baseline
  reviewer over the same diff produces the Track-3 delta metric.

Output: JSON to stdout with keys: verdict, role_findings, metric.
"""

from __future__ import annotations

import argparse
import json
import sys
import pathlib

# Allow `from shared.dashscope import ...` when called as a script from any cwd.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from shared.brain import BrainClient  # noqa: E402

# ---------------------------------------------------------------------------
# Identity / base prompt (from prompts/git-committer/system.md + identity.md)
# ---------------------------------------------------------------------------

_BASE_IDENTITY = (
    "You are git-committer, a specialist code reviewer. "
    "You are terse, precise, and senior. "
    "You do NOT rewrite code; you flag issues and request changes."
)

_ROLE_BRIEFS = [
    (
        "correctness",
        "Find logic bugs, edge cases, off-by-ones, and incorrect behavior. "
        "Be blunt. Examples: 'This will panic on nil input.' "
        "Ignore style and security — that is another reviewer's lane.",
    ),
    (
        "security",
        "Find security holes: injection vectors, auth/authz gaps, hardcoded secrets, "
        "unsafe deserialization, and data exposure. Be paranoid by design. "
        "Hardcoded credentials are always a block. "
        "Ignore style and correctness logic — that is another reviewer's lane.",
    ),
    (
        "style",
        "Find readability problems, naming inconsistencies, dead code, and "
        "missing or inadequate test coverage. Direct. "
        "Examples: 'Rename to fetchUser.', 'No test for the error path. Add one.' "
        "Ignore correctness bugs and security — those are other lanes.",
    ),
]

_ISSUES_SUFFIX = (
    " List concrete issues only. "
    'Respond as strict JSON: {"issues":[{"severity":"high|med|low","note":"..."}]}. '
    "If no issues, respond with: {\"issues\":[]}."
)

_NEGOTIATION_SYSTEM = (
    "You are the reconciliation step for a multi-reviewer code-review panel. "
    "You receive JSON findings from a correctness reviewer, a security reviewer, "
    "and a style/test reviewer. "
    "Deduplicate, rank by severity, resolve disagreements, and produce ONE verdict. "
    'Respond as strict JSON: '
    '{"verdict":"approve|request_changes","summary":"...","ranked_issues":'
    '[{"severity":"high|med|low","note":"...","roles":["..."]}]}.'
)

_BASELINE_SYSTEM = (
    _BASE_IDENTITY
    + " You are doing a single-pass holistic review covering correctness, security, "
    "and style/test coverage together. "
    + _ISSUES_SUFFIX
)


# ---------------------------------------------------------------------------
# Core functions (dependency-injectable client)
# ---------------------------------------------------------------------------


def _parse_issues(raw: str) -> list[dict]:
    """Parse the model's JSON response into a list of issues.

    Parameters:
        raw: The raw JSON string from the model.

    Returns:
        A list of issue dictionaries, or an empty list if parsing fails.
    """
    try:
        data = json.loads(raw)
        return data.get("issues") or []
    except (json.JSONDecodeError, AttributeError):
        return []


def run_role_reviewers(diff: str, client: BrainClient, conventions: str) -> list[dict]:
    """Run role-specific reviewers (correctness, security, style) over the provided diff.

    Parameters:
        diff: The unified diff string to review.
        client: BrainClient instance for making API calls.
        conventions: Code conventions string to guide the reviewers.

    Returns:
        A list of dictionaries, each containing 'role' and 'issues' keys.
    """
    results = []
    for role, brief in _ROLE_BRIEFS:
        system = f"{_BASE_IDENTITY}\n\nYou are the {role} reviewer. {brief}\n\nCode Conventions:\n{conventions}\n{_ISSUES_SUFFIX}"
        prompt = f"Diff:\n{diff}"
        raw = client.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            model="qwen2.5-coder",
            temperature=0,
        )
        results.append({"role": role, "issues": _parse_issues(raw)})
    return results


def run_negotiation(role_findings: list[dict], client: BrainClient) -> dict:
    """Merge findings from role reviewers into a single verdict.

    Parameters:
        role_findings: List of findings from each role reviewer.
        client: BrainClient instance for making API calls.

    Returns:
        A dictionary with 'verdict', 'summary', and 'ranked_issues' keys.
    """
    merged = [
        {**issue, "role": finding["role"]}
        for finding in role_findings
        for issue in finding["issues"]
    ]
    raw = client.chat(
        messages=[
            {"role": "system", "content": _NEGOTIATION_SYSTEM},
            {"role": "user", "content": "Reviewer findings:\n" + json.dumps(merged)},
        ],
        model="qwen2.5-coder",
        temperature=0,
    )
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return {
            "verdict": "request_changes",
            "summary": raw,
            "ranked_issues": [],
        }


def run_baseline(diff: str, client: BrainClient, conventions: str) -> list[dict]:
    """Run a single-agent baseline review over the same diff.

    Parameters:
        diff: The unified diff string to review.
        client: BrainClient instance for making API calls.
        conventions: Code conventions string to guide the reviewer.

    Returns:
        A list of issue dictionaries.
    """
    system = f"{_BASE_IDENTITY} You are doing a single-pass holistic review covering correctness, security, and style/test coverage together. Code Conventions:\n{conventions}\n{_ISSUES_SUFFIX}"
    raw = client.chat(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"Diff:\n{diff}"},
        ],
        model="qwen2.5-coder",
        temperature=0,
    )
    return _parse_issues(raw)


def review_diff(diff: str, client: BrainClient | None = None) -> dict:
    """Run the full review pipeline on a given diff.

    Parameters:
        diff: The unified diff string to review.
        client: Optional BrainClient instance. If None, a new client is created.

    Returns:
        A dictionary with keys:
            - 'verdict', 'role_findings', 'metric' for successful review
            - 'error' if the diff is empty or invalid
    """
    client = client or BrainClient()

    if not diff or not diff.strip():
        return {"error": "empty diff — nothing to review", "verdict": None}

    # Truncate very large diffs to match n8n's 12 000-char ceiling.
    diff = diff[:12_000]

    # Fetch code conventions from BrainClient
    conventions = client.get_code_conventions()

    # --- Role reviewers (parallel in n8n; sequential here) ---
    role_findings = run_role_reviewers(diff, client, conventions)

    # --- Negotiation ---
    verdict = run_negotiation(role_findings, client)

    # --- Baseline ---
    baseline_issues = run_baseline(diff, client, conventions)

    team_count = sum(len(f["issues"]) for f in role_findings)
    baseline_count = len(baseline_issues)

    return {
        "verdict": verdict,
        "role_findings": role_findings,
        "metric": {
            "team_issue_count": team_count,
            "baseline_issue_count": baseline_count,
            "delta": team_count - baseline_count,
        },
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI.

    Parses command-line arguments, reads the diff from file or stdin,
    processes it through the review pipeline, and outputs the result as JSON.

    Args:
        argv: Optional list of command-line arguments. If None, sys.argv is used.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="GIT-Committer multi-agent PR reviewer. Reads a unified diff and prints a JSON verdict."
    )
    parser.add_argument(
        "--diff-file",
        metavar="PATH",
        help="Path to a unified diff file. Reads from stdin if omitted.",
    )
    args = parser.parse_args(argv)

    if args.diff_file:
        diff = pathlib.Path(args.diff_file).read_text(encoding="utf-8")
    else:
        diff = sys.stdin.read()

    result = review_diff(diff)

    if "error" in result and result.get("verdict") is None:
        print(json.dumps(result, indent=2), file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
