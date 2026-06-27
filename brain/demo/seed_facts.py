"""
seed_facts.py — Idempotent fixtures for the MemoryAgent demo.

Clears prior demo rows (agent_id IN ('echo','shared') from memory_facts
and memory_review_queue), then inserts a fresh set of facts across:
  - echo.private
  - shared.code-conventions
  - shared.glossary

Variety: high/low confidence, some expired (expires_at in the past),
         some near-duplicates, a couple pending-only (not promoted here).
"""

import psycopg2
import psycopg2.extras
from brain_client import _get_dsn, ingest_fact

DEMO_AGENTS = ("echo", "shared")
DEMO_NAMESPACES = ("echo.private", "shared.code-conventions", "shared.glossary")


def clear_demo_rows(cur):
    cur.execute(
        "DELETE FROM memory_facts WHERE agent_id = ANY(%s)",
        (list(DEMO_AGENTS),),
    )
    cur.execute(
        "DELETE FROM memory_review_queue WHERE agent_id = ANY(%s)",
        (list(DEMO_AGENTS),),
    )


# ── Seed data ─────────────────────────────────────────────────────────────────

# (agent_id, user_id, memory_namespace, fact_type, subject, predicate, object_text, confidence, expires_at, status)
APPROVED_FACTS = [
    # ── echo.private ──────────────────────────────────────────────────────────
    (
        "echo", "connor", "echo.private", "preference",
        "connor", "prefers", "dark-mode terminals",
        0.950, None, "approved",
    ),
    (
        "echo", "connor", "echo.private", "habit",
        "connor", "starts_day_with", "standup review on Slack",
        0.870, None, "approved",
    ),
    # low confidence — still approved, but shows confidence gradient
    (
        "echo", "connor", "echo.private", "guess",
        "connor", "may_prefer", "four-day workweeks",
        0.310, None, "approved",
    ),
    # EXPIRED — expires_at in the past
    (
        "echo", "connor", "echo.private", "stale-fact",
        "connor", "was_using", "Python 3.9",
        0.900, "2020-01-01 00:00:00+00", "approved",
    ),
    # Another expired, low confidence
    (
        "echo", "connor", "echo.private", "stale-guess",
        "connor", "might_use", "vim as primary editor",
        0.210, "2021-06-01 00:00:00+00", "approved",
    ),

    # ── shared.code-conventions ───────────────────────────────────────────────
    (
        "shared", None, "shared.code-conventions", "convention",
        "python-files", "use_formatter", "black with line-length 100",
        0.990, None, "approved",
    ),
    (
        "shared", None, "shared.code-conventions", "convention",
        "commits", "must_follow", "conventional-commits spec",
        0.980, None, "approved",
    ),
    # Near-duplicate of the above — slightly lower confidence
    (
        "shared", None, "shared.code-conventions", "convention",
        "commits", "should_follow", "conventional-commits spec",
        0.720, None, "approved",
    ),
    (
        "shared", None, "shared.code-conventions", "tooling",
        "ci", "runs_on", "GitHub Actions with ubuntu-latest",
        0.850, None, "approved",
    ),
    # Expired convention
    (
        "shared", None, "shared.code-conventions", "deprecated",
        "tests", "used_framework", "nose (deprecated)",
        0.600, "2022-12-31 00:00:00+00", "approved",
    ),

    # ── shared.glossary ───────────────────────────────────────────────────────
    (
        "shared", None, "shared.glossary", "term",
        "brain", "is_defined_as", "the governed Postgres + Qdrant memory layer",
        0.999, None, "approved",
    ),
    (
        "shared", None, "shared.glossary", "term",
        "echo", "is_defined_as", "the primary AI collaboration agent",
        0.990, None, "approved",
    ),
    (
        "shared", None, "shared.glossary", "term",
        "skippy", "is_defined_as", "the home-ops and banter agent",
        0.990, None, "approved",
    ),
    (
        "shared", None, "shared.glossary", "term",
        "review-queue", "is_defined_as", "staging table for unverified memory candidates",
        0.950, None, "approved",
    ),
    # Low-confidence glossary guess
    (
        "shared", None, "shared.glossary", "guess",
        "n8n", "might_be_replaced_by", "custom orchestrator in future",
        0.200, None, "approved",
    ),
]


def seed():
    conn = psycopg2.connect(**_get_dsn())
    try:
        with conn.cursor() as cur:
            clear_demo_rows(cur)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    # Ingest facts via the brain client's API
    for fact in APPROVED_FACTS:
        ingest_fact(*fact)
    print(f"[seed] Inserted {len(APPROVED_FACTS)} facts via ingest API.")


if __name__ == "__main__":
    seed()
