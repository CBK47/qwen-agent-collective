"""Tests for agents/git-committer/review.py.

Run from repo root:
    python tests/test_git_committer.py

Also pytest-discoverable.

Uses a FakeClient so no DASHSCOPE_API_KEY is required.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

# ---------------------------------------------------------------------------
# Load the module from a hyphenated directory (not an importable package).
# ---------------------------------------------------------------------------

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_REVIEW_PATH = _REPO_ROOT / "agents" / "git-committer" / "review.py"

spec = importlib.util.spec_from_file_location("git_committer_review", _REVIEW_PATH)
review_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review_mod)

review_diff = review_mod.review_diff
run_role_reviewers = review_mod.run_role_reviewers
run_debate = review_mod.run_debate
run_negotiation = review_mod.run_negotiation
run_baseline = review_mod.run_baseline

# ---------------------------------------------------------------------------
# FakeClient — disambiguates calls by prompt content
# ---------------------------------------------------------------------------

ROLE_RESPONSE = json.dumps({"issues": [{"severity": "high", "note": "test issue"}]})
REBUTTAL_RESPONSE = json.dumps({
    "issues": [{"severity": "high", "note": "test issue"}],
    "stance": "defended my finding",
})
# Negotiator dedupes the 3 role findings into 2 ranked issues; baseline finds 1
# → team 2, baseline 1, delta 1.
NEGOTIATION_RESPONSE = json.dumps({
    "verdict": "request_changes",
    "summary": "One high-severity issue found.",
    "commit_message": "fix(foo): remove hardcoded credential from greet",
    "ranked_issues": [
        {"severity": "high", "note": "test issue", "roles": ["correctness", "security"]},
        {"severity": "med", "note": "style issue", "roles": ["style"]},
    ],
})
BASELINE_RESPONSE = json.dumps({"issues": [{"severity": "med", "note": "baseline catch"}]})


class FakeClient:
    """Dependency-injected fake that returns canned JSON without a live API key."""

    config = type("C", (), {"coder_model": "c", "chat_model": "p"})()

    def get_code_conventions(self) -> str:
        return "fake conventions"

    def chat(self, prompt=None, *, messages=None, model=None, **kw) -> str:
        # Determine call type from the system message content.
        system_content = ""
        if messages:
            for m in messages:
                if m.get("role") == "system":
                    system_content = m.get("content", "")
                    break
        # Fall back to prompt string if messages not supplied.
        text = system_content or (prompt or "")

        # "reconciliation step" appears in _NEGOTIATION_SYSTEM; "Reviewer findings:" is the user turn
        if "reconciliation" in text.lower() or "reviewer findings" in text.lower():
            return NEGOTIATION_RESPONSE
        if "single-pass holistic" in text:
            return BASELINE_RESPONSE
        # "Re-examine the diff" appears in _REBUTTAL_SUFFIX
        if "re-examine the diff" in text.lower():
            return REBUTTAL_RESPONSE
        # Default: role reviewer response
        return ROLE_RESPONSE


SAMPLE_DIFF = """\
diff --git a/foo.py b/foo.py
index 0000000..1111111 100644
--- a/foo.py
+++ b/foo.py
@@ -1,3 +1,5 @@
 def greet(name):
-    return "Hello " + name
+    password = "secret123"  # hardcoded credential
+    return "Hello " + name + password
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_role_reviewers_returns_three_results():
    """run_role_reviewers must return exactly 3 role dicts."""
    fake = FakeClient()
    results = run_role_reviewers(SAMPLE_DIFF, fake)
    assert len(results) == 3, f"Expected 3 role results, got {len(results)}"
    roles = [r["role"] for r in results]
    assert "correctness" in roles
    assert "security" in roles
    assert "style" in roles
    for r in results:
        assert isinstance(r["issues"], list), f"issues not a list for role {r['role']}"


def test_negotiation_produces_verdict():
    """run_negotiation must return a dict with a 'verdict' key."""
    fake = FakeClient()
    role_findings = [
        {"role": "correctness", "issues": [{"severity": "high", "note": "bug"}]},
        {"role": "security", "issues": []},
        {"role": "style", "issues": []},
    ]
    verdict = run_negotiation(role_findings, fake)
    assert "verdict" in verdict, "Negotiation result missing 'verdict'"
    assert verdict["verdict"] in ("approve", "request_changes", "block"), (
        f"Unexpected verdict value: {verdict['verdict']}"
    )


def test_baseline_metric_delta():
    """review_diff metric delta must equal team_issue_count - baseline_issue_count."""
    fake = FakeClient()
    result = review_diff(SAMPLE_DIFF, fake)

    assert "error" not in result, f"Unexpected error: {result.get('error')}"

    metric = result["metric"]
    expected_delta = metric["team_issue_count"] - metric["baseline_issue_count"]
    assert metric["delta"] == expected_delta, (
        f"delta {metric['delta']} != team {metric['team_issue_count']} "
        f"- baseline {metric['baseline_issue_count']}"
    )

    # Team count is the negotiator's DEDUPLICATED ranked issues (2), not the raw
    # per-role sum (3) — three roles flagging the same secret count once.
    assert metric["team_issue_count"] == 2, f"Expected 2 team issues, got {metric['team_issue_count']}"
    assert metric["first_pass_issue_count"] == 3, (
        f"Expected 3 first-pass issues, got {metric['first_pass_issue_count']}"
    )
    assert metric["baseline_issue_count"] == 1, f"Expected 1 baseline issue, got {metric['baseline_issue_count']}"
    assert metric["delta"] == 1, f"Expected delta 1, got {metric['delta']}"


def test_debate_round_in_output():
    """review_diff must include a debate entry per role, each with a stance."""
    fake = FakeClient()
    result = review_diff(SAMPLE_DIFF, fake)
    debate = result.get("debate")
    assert isinstance(debate, list) and len(debate) == 3, f"Expected 3 debate entries, got {debate}"
    for entry in debate:
        assert entry["role"] in ("correctness", "security", "style")
        assert isinstance(entry["issues"], list)
        assert entry["stance"], f"Empty stance for role {entry['role']}"


def test_commit_message_in_verdict():
    """The negotiated verdict must carry a Conventional Commits message."""
    fake = FakeClient()
    result = review_diff(SAMPLE_DIFF, fake)
    msg = result["verdict"].get("commit_message", "")
    assert msg.startswith("fix("), f"Unexpected commit message: {msg!r}"


def test_json_fence_tolerated():
    """_extract_json must survive ```json fences around the model response."""
    fenced = "```json\n" + ROLE_RESPONSE + "\n```"
    issues = review_mod._parse_issues(fenced)
    assert len(issues) == 1, f"Fenced JSON not parsed: {issues}"


def test_json_multiple_blocks_tolerated():
    """_extract_json must parse the first balanced object, not first-{ to last-}.

    Regression: reviewing a diff that itself quotes JSON templates made the
    response contain several JSON-looking fragments; first-{..last-} spanned
    them all, failed to parse, and findings were silently dropped.
    """
    noisy = "Here is my finding:\n" + ROLE_RESPONSE + '\nas required by {"issues":[...]} format.'
    issues = review_mod._parse_issues(noisy)
    assert len(issues) == 1, f"Multi-block response not parsed: {issues}"
    # Braces and escaped quotes inside JSON strings must not confuse the scan.
    tricky = json.dumps({"issues": [{"severity": "low", "note": 'say "hi" } and { \\ done'}]})
    assert len(review_mod._parse_issues("x " + tricky + " y")) == 1


def test_empty_diff_guarded():
    """review_diff must return an error object (not raise) for empty input."""
    fake = FakeClient()

    # empty string
    result_empty = review_diff("", fake)
    assert "error" in result_empty, "Empty diff did not return an error object"
    assert result_empty["verdict"] is None

    # whitespace-only
    result_ws = review_diff("   \n\t  ", fake)
    assert "error" in result_ws, "Whitespace-only diff did not return an error object"


def test_role_findings_in_output():
    """review_diff result must contain role_findings list."""
    fake = FakeClient()
    result = review_diff(SAMPLE_DIFF, fake)
    assert "role_findings" in result, "Missing role_findings in output"
    assert isinstance(result["role_findings"], list)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_role_reviewers_returns_three_results,
        test_negotiation_produces_verdict,
        test_baseline_metric_delta,
        test_debate_round_in_output,
        test_commit_message_in_verdict,
        test_json_fence_tolerated,
        test_json_multiple_blocks_tolerated,
        test_empty_diff_guarded,
        test_role_findings_in_output,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
            passed += 1
        except Exception as exc:
            print(f"FAIL  {t.__name__}: {exc}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
