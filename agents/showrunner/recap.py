"""agents/showrunner/recap.py — Showrunner nightly recap CLI (Track 2, text-first MVP).

Mirrors the logic of brain/orchestrator/workflows/showrunner-recap-nightly.json but runs
from the command line using a local events JSON file instead of a live Postgres query.

Usage:
    python agents/showrunner/recap.py --events agents/showrunner/sample-events.json
    python agents/showrunner/recap.py --events my-events.json --max-events 50 --date 2026-06-27

Requires: DASHSCOPE_API_KEY in environment or .env (not needed for tests — inject FakeClient).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import date, timezone
from typing import Any

# Allow `from shared.xxx import ...` when running this file directly.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from shared.dashscope import DashScopeClient  # noqa: E402
from shared.namespaces import SHOWRUNNER_PRIVATE  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_HERE = pathlib.Path(__file__).resolve().parent
EPISODES_DIR = _HERE / "episodes"
REGISTRY_PATH = EPISODES_DIR / "registry.json"
SYSTEM_PROMPT_PATH = pathlib.Path(__file__).resolve().parents[2] / "prompts" / "showrunner" / "system.md"

# ---------------------------------------------------------------------------
# Token-budget constants
# ---------------------------------------------------------------------------
DEFAULT_MAX_EVENTS = 120          # cap passed in from n8n; overridable via CLI / tests
FIELD_TRUNCATE_CHARS = 160        # truncate event_text to this many chars (budget discipline)


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_events(path: str | pathlib.Path) -> list[dict[str, Any]]:
    """Load memory_events rows from a JSON file.

    TODO: query memory_events from the brain over a time window, e.g.:
        SELECT agent_id, event_type, title, event_text, event_time
        FROM memory_events
        WHERE event_time > NOW() - INTERVAL '24 hours'
        ORDER BY event_time ASC
        LIMIT 200;
    Replace this function with a Postgres call once the brain is live.
    """
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def apply_token_budget(events: list[dict[str, Any]], max_events: int) -> list[dict[str, Any]]:
    """Cap to *max_events* and truncate long fields — the Track-2 token-budget step.

    The cap is the primary lever; field truncation keeps individual events compact so
    the prompt stays well within the model's context window even at max budget.
    """
    capped = events[:max_events]
    budgeted: list[dict[str, Any]] = []
    for row in capped:
        budgeted.append({
            "agent_id": str(row.get("agent_id", "")).strip(),
            "event_type": str(row.get("event_type", "")).strip(),
            "title": str(row.get("title", "")).strip()[:80],
            "event_text": str(row.get("event_text", "")).strip()[:FIELD_TRUNCATE_CHARS],
            "event_time": str(row.get("event_time", "")).strip(),
        })
    return budgeted


def build_context_bundle(events: list[dict[str, Any]]) -> str:
    """Format the budgeted events into the user-turn context string."""
    if not events:
        return "(a quiet day — note it briefly)"
    lines = [
        f"- [{r['event_type']}] {r['agent_id']} @ {r['event_time']}: "
        f"{r['title']} — {r['event_text']}"
        for r in events
    ]
    return "Events (last 24 h):\n" + "\n".join(lines)


def load_system_prompt() -> str:
    """Load prompts/showrunner/system.md, falling back to an inline default."""
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    # Inline fallback — keeps the agent runnable if the prompt file moves.
    return (
        "You are The Showrunner. Turn the agent society's day into a short, vivid "
        "recap episode in markdown: a '# title', 3-5 beat bullets, and a one-line "
        "teaser. Under 200 words. Invent nothing not in the events."
    )


# ---------------------------------------------------------------------------
# Core logic (dependency-injectable for tests)
# ---------------------------------------------------------------------------

class ShowrunnerRecap:
    """Orchestrates the nightly recap pipeline."""

    def __init__(self, client: DashScopeClient | None = None):
        # Dependency-inject the client so tests can pass a FakeClient.
        self.client = client or DashScopeClient()

    def generate_episode(
        self,
        events: list[dict[str, Any]],
        *,
        max_events: int = DEFAULT_MAX_EVENTS,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Run the scriptwriter step.

        Returns (recap_markdown, budgeted_events).
        The budgeted_events list is returned so callers / tests can inspect the budget.
        """
        budgeted = apply_token_budget(events, max_events)
        context = build_context_bundle(budgeted)
        system_voice = load_system_prompt()

        # Keep the prompt lean — that's the Track-2 point.
        recap_md = self.client.chat(
            messages=[
                {"role": "system", "content": system_voice},
                {
                    "role": "user",
                    "content": (
                        context + "\n\n"
                        "Produce a short markdown recap episode: a `# title`, "
                        "3-5 beat bullets, and a one-line teaser. Under 200 words. "
                        "Invent nothing not in the events."
                    ),
                },
            ],
            model=self.client.config.chat_model,
            temperature=0.7,
            max_tokens=512,
        )
        return recap_md, budgeted

    def write_journal(
        self,
        recap_md: str,
        *,
        episode_date: str | None = None,
        episodes_dir: pathlib.Path = EPISODES_DIR,
    ) -> pathlib.Path:
        """Write the recap markdown to episodes/<date>.md."""
        episodes_dir.mkdir(parents=True, exist_ok=True)
        ep_date = episode_date or date.today().isoformat()
        journal_path = episodes_dir / f"{ep_date}.md"
        journal_path.write_text(recap_md, encoding="utf-8")
        return journal_path

    def update_registry(
        self,
        *,
        title: str,
        episode_date: str,
        event_count: int,
        journal_path: pathlib.Path,
        registry_path: pathlib.Path = REGISTRY_PATH,
        episodes_dir: pathlib.Path = EPISODES_DIR,
    ) -> None:
        """Append an entry to episodes/registry.json.

        Namespace: showrunner.private (SHOWRUNNER_PRIVATE).

        TODO: also write this entry to the brain's memory_facts table:
            INSERT INTO memory_facts (agent_id, memory_namespace, fact_type, subject,
                predicate, object_text, confidence, status)
            VALUES ('showrunner', 'showrunner.private', 'episode', <title>,
                'recap', <recap_md>, 0.9, 'approved');
        """
        episodes_dir.mkdir(parents=True, exist_ok=True)
        existing: list[dict[str, Any]] = []
        if registry_path.exists():
            try:
                existing = json.loads(registry_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                existing = []

        existing.append({
            "namespace": SHOWRUNNER_PRIVATE,
            "title": title,
            "date": episode_date,
            "event_count": event_count,
            "file": str(journal_path),
        })
        registry_path.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def run(
        self,
        events_path: str | pathlib.Path,
        *,
        max_events: int = DEFAULT_MAX_EVENTS,
        episode_date: str | None = None,
        episodes_dir: pathlib.Path = EPISODES_DIR,
        registry_path: pathlib.Path = REGISTRY_PATH,
    ) -> dict[str, Any]:
        """End-to-end pipeline: load → budget → scriptwrite → journal → registry."""
        events = load_events(events_path)
        total_events = len(events)

        recap_md, budgeted = self.generate_episode(events, max_events=max_events)

        # Extract the title from the first markdown heading, fall back gracefully.
        title_line = next(
            (line.lstrip("# ").strip() for line in recap_md.splitlines() if line.startswith("#")),
            "Daily recap",
        )
        title = title_line[:120]

        ep_date = episode_date or date.today().isoformat()

        journal_path = self.write_journal(
            recap_md,
            episode_date=ep_date,
            episodes_dir=episodes_dir,
        )

        self.update_registry(
            title=title,
            episode_date=ep_date,
            event_count=len(budgeted),
            journal_path=journal_path,
            registry_path=registry_path,
            episodes_dir=episodes_dir,
        )

        return {
            "events_read": total_events,
            "events_used": len(budgeted),
            "title": title,
            "journal_path": str(journal_path),
        }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Showrunner nightly recap — text-first MVP (Track 2).",
    )
    parser.add_argument(
        "--events",
        required=True,
        metavar="PATH",
        help="JSON file of memory_events rows (agent_id, event_type, title, event_text, event_time).",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=DEFAULT_MAX_EVENTS,
        metavar="N",
        help=f"Token-budget cap: use at most N events (default {DEFAULT_MAX_EVENTS}).",
    )
    parser.add_argument(
        "--date",
        default=None,
        metavar="YYYY-MM-DD",
        help="Episode date (default: today).",
    )
    args = parser.parse_args(argv)

    recap = ShowrunnerRecap()
    result = recap.run(
        args.events,
        max_events=args.max_events,
        episode_date=args.date,
    )

    print(f"Events read  : {result['events_read']}")
    print(f"Events used  : {result['events_used']} (budget cap: {args.max_events})")
    print(f"Episode title: {result['title']}")
    print(f"Journal path : {result['journal_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
