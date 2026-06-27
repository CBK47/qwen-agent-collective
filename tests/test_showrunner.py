"""tests/test_showrunner.py — Unit tests for agents/showrunner/recap.py.

Run from repo root:
    python tests/test_showrunner.py

All tests use a FakeClient (no live DashScope calls required).
Test artifacts are written to a temp dir, not the real episodes/ directory.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

# ---------------------------------------------------------------------------
# Load agents/showrunner/recap.py via importlib so the hyphen-free path works
# and so this test file doesn't need __init__ adjustments.
# ---------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_RECAP_PATH = _REPO_ROOT / "agents" / "showrunner" / "recap.py"

# Add repo root to sys.path so shared.* imports inside recap.py resolve.
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

spec = importlib.util.spec_from_file_location("showrunner_recap", _RECAP_PATH)
recap_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recap_mod)

ShowrunnerRecap = recap_mod.ShowrunnerRecap
apply_token_budget = recap_mod.apply_token_budget
build_context_bundle = recap_mod.build_context_bundle
load_events = recap_mod.load_events

# ---------------------------------------------------------------------------
# Fake DashScope client — records the last prompt passed to .chat()
# ---------------------------------------------------------------------------
CANNED_EPISODE = (
    "# The Night the Door Said No\n"
    "- Echo surfaced a long-forgotten preference that changed everything.\n"
    "- git-committer blocked the auth-service PR on a hardcoded constant.\n"
    "- Skippy refused the midnight unlock — policy over convenience.\n"
    "- open-translate quietly expanded the shared glossary.\n"
    "Teaser: tomorrow, the PR waits."
)


class FakeConfig:
    chat_model = "qwen-plus"


class FakeDashScopeClient:
    """Minimal stand-in for shared.dashscope.DashScopeClient."""

    def __init__(self):
        self.config = FakeConfig()
        self.last_messages: list[dict] | None = None
        self.last_prompt: str | None = None

    def chat(
        self,
        prompt: str | None = None,
        *,
        messages=None,
        model=None,
        temperature=None,
        max_tokens=None,
        **_,
    ) -> str:
        self.last_messages = messages
        self.last_prompt = prompt
        return CANNED_EPISODE


# ---------------------------------------------------------------------------
# Helper: build a list of N minimal event dicts
# ---------------------------------------------------------------------------
def _make_events(n: int) -> list[dict]:
    agents = ["echo", "git-committer", "open-translate", "showrunner", "skippy"]
    return [
        {
            "agent_id": agents[i % len(agents)],
            "event_type": "session_summary",
            "title": f"Event {i}",
            "event_text": f"Something happened in event {i}.",
            "event_time": f"2026-06-27T{i % 24:02d}:00:00Z",
        }
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTokenBudget(unittest.TestCase):
    """apply_token_budget must honour the cap."""

    def test_cap_respected(self):
        events = _make_events(200)
        budgeted = apply_token_budget(events, max_events=50)
        self.assertEqual(len(budgeted), 50)

    def test_fewer_than_cap(self):
        events = _make_events(10)
        budgeted = apply_token_budget(events, max_events=50)
        self.assertEqual(len(budgeted), 10)

    def test_field_truncation(self):
        events = [
            {
                "agent_id": "echo",
                "event_type": "session_summary",
                "title": "x" * 200,
                "event_text": "y" * 500,
                "event_time": "2026-06-27T00:00:00Z",
            }
        ]
        budgeted = apply_token_budget(events, max_events=10)
        self.assertLessEqual(len(budgeted[0]["title"]), 80)
        self.assertLessEqual(len(budgeted[0]["event_text"]), recap_mod.FIELD_TRUNCATE_CHARS)


class TestContextBundle(unittest.TestCase):
    """build_context_bundle produces the right text."""

    def test_empty_events(self):
        bundle = build_context_bundle([])
        self.assertIn("quiet", bundle)

    def test_contains_all_events(self):
        events = apply_token_budget(_make_events(5), max_events=10)
        bundle = build_context_bundle(events)
        for i in range(5):
            self.assertIn(f"Event {i}", bundle)


class TestGenerateEpisode(unittest.TestCase):
    """generate_episode: FakeClient receives a prompt containing ≤ max_events events."""

    def setUp(self):
        self.fake_client = FakeDashScopeClient()
        self.recap = ShowrunnerRecap(client=self.fake_client)

    def test_budget_enforced_in_prompt(self):
        """The text sent to the model must not contain more events than the budget."""
        budget = 5
        events = _make_events(20)  # give it MORE than the budget
        recap_md, budgeted = self.recap.generate_episode(events, max_events=budget)

        # (1) Budget respected: budgeted list is capped
        self.assertLessEqual(len(budgeted), budget)

        # Also verify the prompt text only references at most `budget` events.
        # The messages list contains the user turn with the context bundle.
        user_content = next(
            m["content"] for m in self.fake_client.last_messages if m["role"] == "user"
        )
        # Count how many "Event N" markers appear — each maps to one event row.
        event_markers = [f"Event {i}" for i in range(20) if f"Event {i}" in user_content]
        self.assertLessEqual(len(event_markers), budget)

    def test_recap_content_returned(self):
        events = _make_events(3)
        recap_md, _ = self.recap.generate_episode(events, max_events=10)
        self.assertEqual(recap_md, CANNED_EPISODE)
        self.assertIn("# ", recap_md)

    def test_system_prompt_included(self):
        """The system voice must be passed as a system message."""
        events = _make_events(3)
        self.recap.generate_episode(events, max_events=10)
        roles = [m["role"] for m in self.fake_client.last_messages]
        self.assertIn("system", roles)


class TestWriteJournalAndRegistry(unittest.TestCase):
    """End-to-end run() writes journal file and registry entry to a temp dir."""

    def setUp(self):
        self.fake_client = FakeDashScopeClient()
        self.recap = ShowrunnerRecap(client=self.fake_client)
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._tmpdir.name)
        self.episodes_dir = self.tmp / "episodes"
        self.registry_path = self.episodes_dir / "registry.json"

    def tearDown(self):
        self._tmpdir.cleanup()

    def _run(self, n_events=10, max_events=5, ep_date="2026-06-27"):
        # Write a temporary events file
        events_file = self.tmp / "events.json"
        events_file.write_text(json.dumps(_make_events(n_events)), encoding="utf-8")
        return self.recap.run(
            events_file,
            max_events=max_events,
            episode_date=ep_date,
            episodes_dir=self.episodes_dir,
            registry_path=self.registry_path,
        )

    def test_journal_file_created(self):
        """(2) A recap episode is produced and written to the journal."""
        result = self._run()
        journal_path = pathlib.Path(result["journal_path"])
        self.assertTrue(journal_path.exists(), "Journal file was not created")
        content = journal_path.read_text(encoding="utf-8")
        self.assertEqual(content, CANNED_EPISODE)

    def test_registry_entry_appended(self):
        """(3) The registry gains an entry after a run."""
        self._run(ep_date="2026-06-27")
        self.assertTrue(self.registry_path.exists(), "Registry file was not created")
        entries = json.loads(self.registry_path.read_text(encoding="utf-8"))
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["date"], "2026-06-27")
        self.assertIn("title", entry)
        self.assertIn("event_count", entry)
        self.assertIn("file", entry)
        from shared.namespaces import SHOWRUNNER_PRIVATE
        self.assertEqual(entry["namespace"], SHOWRUNNER_PRIVATE)

    def test_registry_accumulates_runs(self):
        """Multiple runs accumulate entries in the registry."""
        self._run(ep_date="2026-06-26")
        self._run(ep_date="2026-06-27")
        entries = json.loads(self.registry_path.read_text(encoding="utf-8"))
        self.assertEqual(len(entries), 2)

    def test_budget_reflected_in_result(self):
        """events_used must be <= max_events even when events_read > max_events."""
        result = self._run(n_events=20, max_events=7)
        self.assertEqual(result["events_read"], 20)
        self.assertLessEqual(result["events_used"], 7)

    def test_summary_fields_present(self):
        result = self._run()
        for key in ("events_read", "events_used", "title", "journal_path"):
            self.assertIn(key, result)


class TestLoadEvents(unittest.TestCase):
    """load_events reads the sample fixture without error."""

    def test_sample_fixture_loads(self):
        fixture = _REPO_ROOT / "agents" / "showrunner" / "sample-events.json"
        self.assertTrue(fixture.exists(), "sample-events.json missing")
        events = load_events(fixture)
        self.assertGreater(len(events), 0)
        for row in events:
            for field in ("agent_id", "event_type", "title", "event_text", "event_time"):
                self.assertIn(field, row, f"Missing field '{field}' in row: {row}")

    def test_known_agent_ids_present(self):
        fixture = _REPO_ROOT / "agents" / "showrunner" / "sample-events.json"
        events = load_events(fixture)
        agent_ids = {e["agent_id"] for e in events}
        expected = {"echo", "git-committer", "open-translate", "showrunner", "skippy"}
        self.assertTrue(
            expected.issubset(agent_ids),
            f"Missing agent ids. Found: {agent_ids}",
        )


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
