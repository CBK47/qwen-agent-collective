"""GIT-Committer · Multi-Agent PR Review CLI (Track 3).

Usage:
    python agents/git-committer/review.py --diff-file sample.patch
    git diff HEAD~1 | python agents/git-committer/review.py

Pipeline (task division → dialogue → negotiation, per the Track 3 brief):
  1. Three role reviewers (correctness, security, style/test-coverage) review
     the same diff in parallel.
  2. Debate round: each reviewer sees its peers' findings and revises its own —
     conceding duplicates, defending disputed calls, adding what the discussion
     revealed.
  3. A negotiation step merges the post-debate findings into one verdict plus a
     Conventional Commits message.
  4. A single-agent baseline reviews the same diff; the deduplicated team
     finding count vs the baseline count is the Agent Society delta metric.

Output: JSON to stdout with keys: verdict, role_findings, debate, metric.
"""

from __future__ import annotations

import argparse
import json
import sys
import pathlib
from concurrent.futures import ThreadPoolExecutor

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

_REBUTTAL_SUFFIX = (
    " You already reviewed this diff once. Now you can see your peers' findings. "
    "Re-examine the diff in light of them: drop your findings that a peer covers "
    "better or that you no longer stand by, keep the ones you defend, and add "
    "anything the peer discussion revealed in YOUR lane only. "
    'Respond as strict JSON: {"issues":[{"severity":"high|med|low","note":"..."}],'
    '"stance":"one short line on what you conceded or defended"}.'
)

_NEGOTIATION_SYSTEM = (
    "You are the reconciliation step for a multi-reviewer code-review panel. "
    "You receive post-debate JSON findings from a correctness reviewer, a security "
    "reviewer, and a style/test reviewer. "
    "Merge duplicates (the SAME defect reported by multiple roles) into one entry, "
    "but NEVER combine different defects into one entry — one ranked issue per "
    "distinct defect. Rank by severity, resolve disagreements, and produce ONE verdict. "
    "Also write a Conventional Commits message for the diff itself "
    "(type(scope): subject, subject <= 72 chars, imperative mood). "
    'Respond as strict JSON: '
    '{"verdict":"approve|request_changes","summary":"...","commit_message":"...",'
    '"ranked_issues":[{"severity":"high|med|low","note":"...","roles":["..."]}]}.'
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


def _extract_json(raw: str) -> dict:
    """Parse a JSON object out of a model response, tolerating ``` fences and prose."""
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object in model response")
    return json.loads(raw[start : end + 1])


def _parse_issues(raw: str) -> list[dict]:
    """Parse the model's JSON response into a list of issues.

    Parameters:
        raw: The raw JSON string from the model.

    Returns:
        A list of issue dictionaries, or an empty list if parsing fails.
    """
    try:
        data = _extract_json(raw)
        return data.get("issues") or []
    except (ValueError, json.JSONDecodeError, AttributeError):
        return []


def run_role_reviewers(diff: str, client: BrainClient, conventions: str = "") -> list[dict]:
    """Run role-specific reviewers (correctness, security, style) over the provided diff.

    Parameters:
        diff: The unified diff string to review.
        client: BrainClient instance for making API calls.
        conventions: Code conventions string to guide the reviewers.

    Returns:
        A list of dictionaries, each containing 'role' and 'issues' keys.
    """
    def review_one(role: str, brief: str) -> dict:
        system = f"{_BASE_IDENTITY}\n\nYou are the {role} reviewer. {brief}\n\nCode Conventions:\n{conventions}\n{_ISSUES_SUFFIX}"
        raw = client.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Diff:\n{diff}"},
            ],
            model=getattr(client.config, "coder_model", "qwen2.5-coder"),
            temperature=0,
        )
        return {"role": role, "issues": _parse_issues(raw)}

    with ThreadPoolExecutor(max_workers=len(_ROLE_BRIEFS)) as pool:
        return list(pool.map(lambda rb: review_one(*rb), _ROLE_BRIEFS))


def run_debate(diff: str, role_findings: list[dict], client: BrainClient, conventions: str = "") -> list[dict]:
    """One rebuttal round: each reviewer sees its peers' findings and revises its own.

    This is the 'dialogue' step of the Track 3 pipeline — reviewers concede
    duplicates, defend disputed calls, or add issues the discussion surfaced.

    Parameters:
        diff: The unified diff string under review.
        role_findings: First-pass findings from run_role_reviewers.
        client: BrainClient instance for making API calls.
        conventions: Code conventions string to guide the reviewers.

    Returns:
        A list of dicts with 'role', 'issues' (revised), and 'stance' keys.
    """
    def rebut(role: str, brief: str) -> dict:
        own = next((f["issues"] for f in role_findings if f["role"] == role), [])
        peers = {f["role"]: f["issues"] for f in role_findings if f["role"] != role}
        system = f"{_BASE_IDENTITY}\n\nYou are the {role} reviewer. {brief}\n\nCode Conventions:\n{conventions}\n{_REBUTTAL_SUFFIX}"
        user = (
            f"Diff:\n{diff}\n\n"
            f"Your first-pass findings:\n{json.dumps(own)}\n\n"
            f"Peer findings:\n{json.dumps(peers)}"
        )
        raw = client.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            model=getattr(client.config, "coder_model", "qwen2.5-coder"),
            temperature=0,
        )
        try:
            data = _extract_json(raw)
        except (ValueError, json.JSONDecodeError):
            data = {"issues": own, "stance": "response unparseable — kept first-pass findings"}
        return {"role": role, "issues": data.get("issues") or [], "stance": str(data.get("stance", ""))}

    with ThreadPoolExecutor(max_workers=len(_ROLE_BRIEFS)) as pool:
        return list(pool.map(lambda rb: rebut(*rb), _ROLE_BRIEFS))


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
        model=getattr(client.config, "coder_model", "qwen2.5-coder"),
        temperature=0,
    )
    try:
        return _extract_json(raw)
    except (ValueError, json.JSONDecodeError):
        return {
            "verdict": "request_changes",
            "summary": raw,
            "commit_message": "",
            "ranked_issues": [],
        }


def run_baseline(diff: str, client: BrainClient, conventions: str = "") -> list[dict]:
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
        model=getattr(client.config, "coder_model", "qwen2.5-coder"),
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
            - 'verdict', 'role_findings', 'debate', 'metric' for successful review
            - 'error' if the diff is empty or invalid
    """
    client = client or BrainClient()

    if not diff or not diff.strip():
        return {"error": "empty diff — nothing to review", "verdict": None}

    # Truncate very large diffs to match n8n's 12 000-char ceiling.
    diff = diff[:12_000]

    # Fetch code conventions from BrainClient
    conventions = client.get_code_conventions()

    # --- Task division: parallel role reviewers ---
    role_findings = run_role_reviewers(diff, client, conventions)

    # --- Dialogue: rebuttal round over peers' findings ---
    debate = run_debate(diff, role_findings, client, conventions)

    # --- Negotiation: merge post-debate findings into one verdict ---
    verdict = run_negotiation(debate, client)

    # --- Baseline ---
    baseline_issues = run_baseline(diff, client, conventions)

    # Deduplicated team count: the negotiator's ranked issues, so three roles
    # flagging the same secret count once — an honest delta vs the baseline.
    team_count = len(verdict.get("ranked_issues") or [])
    baseline_count = len(baseline_issues)

    return {
        "verdict": verdict,
        "role_findings": role_findings,
        "debate": debate,
        "metric": {
            "team_issue_count": team_count,
            "first_pass_issue_count": sum(len(f["issues"]) for f in role_findings),
            "baseline_issue_count": baseline_count,
            "delta": team_count - baseline_count,
        },
    }


def format_review_report(result: dict) -> str:
    """Render review output as a compact human-readable report for demos."""
    if result.get("error"):
        return result["error"]

    verdict = result.get("verdict") or {}
    metric = result.get("metric") or {}
    lines = [
        f"Verdict: {verdict.get('verdict', 'unknown')}",
        f"Summary: {verdict.get('summary', '').strip() or 'No summary returned.'}",
    ]

    commit_message = (verdict.get("commit_message") or "").strip()
    if commit_message:
        lines.extend(["", f"Suggested commit: {commit_message}"])

    lines.extend(["", "First-pass findings:"])
    for finding in result.get("role_findings", []):
        issues = finding.get("issues") or []
        lines.append(f"- {finding.get('role', 'unknown')}: {len(issues)} issue(s)")

    debate = result.get("debate") or []
    if debate:
        lines.extend(["", "Debate round:"])
        for entry in debate:
            issues = entry.get("issues") or []
            stance = (entry.get("stance") or "").strip()
            lines.append(f"- {entry.get('role', 'unknown')} kept {len(issues)} issue(s): {stance}")

    ranked = verdict.get("ranked_issues") or []
    if ranked:
        lines.extend(["", "Negotiated issues:"])
        for issue in ranked:
            severity = issue.get("severity", "unknown")
            note = issue.get("note", "").strip()
            lines.append(f"  [{severity}] {note}")

    lines.extend([
        "",
        "Agent Society delta (deduplicated team vs single agent):",
        f"- team issue count: {metric.get('team_issue_count', 0)}",
        f"- single-agent baseline count: {metric.get('baseline_issue_count', 0)}",
        f"- delta: {metric.get('delta', 0)}",
    ])
    return "\n".join(lines)


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
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format. JSON is the judging/test default; text is for demo UI.",
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

    if args.format == "text":
        print(format_review_report(result))
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
