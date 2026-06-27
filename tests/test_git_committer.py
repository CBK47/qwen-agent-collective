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
run_negotiation = review_mod.run_negotiation
run_baseline = review_mod.run_baseline

# ---------------------------------------------------------------------------
# FakeClient — disambiguates calls by prompt content
# ---------------------------------------------------------------------------

ROLE_RESPONSE = json.dumps({"issues": [{"severity": "high", "note": "test issue"}]})
NEGOTIATION_RESPONSE = json.dumps({
    "verdict": "request_changes",
    "summary": "One high-severity issue found.",
    "ranked_issues": [{"severity": "high", "note": "test issue", "roles": ["correctness"]}],
})
# baseline returns 1 issue (less than team total of 3) → delta = 3 - 1 = 2
BASELINE_RESPONSE = json.dumps({"issues": [{"severity": "med", "note": "baseline catch"}]})


class FakeClient:
    """Dependency-injected fake that returns canned JSON without a live API key."""

    config = type("C", (), {"coder_model": "c", "chat_model": "p"})()

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

    # With FakeClient: 3 roles × 1 issue each = 3 team; 1 baseline issue → delta = 2
    assert metric["team_issue_count"] == 3, f"Expected 3 team issues, got {metric['team_issue_count']}"
    assert metric["baseline_issue_count"] == 1, f"Expected 1 baseline issue, got {metric['baseline_issue_count']}"
    assert metric["delta"] == 2, f"Expected delta 2, got {metric['delta']}"


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
