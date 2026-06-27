"""
brain_client.py — Thin Postgres client for the MemoryAgent demo.

Reads connection details from environment variables with sensible defaults:
  POSTGRES_HOST     default: localhost
  POSTGRES_PORT     default: 5432
  POSTGRES_DB       default: collective
  POSTGRES_USER     default: collective
  POSTGRES_PASSWORD default: change-me
"""

import json
import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from typing import Any

# ── connection ────────────────────────────────────────────────────────────────

def _get_dsn() -> dict:
    return dict(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "collective"),
        user=os.getenv("POSTGRES_USER", "collective"),
        password=os.getenv("POSTGRES_PASSWORD", "change-me"),
    )


@contextmanager
def _conn():
    """Context manager: yield a psycopg2 connection, commit on exit."""
    conn = psycopg2.connect(**_get_dsn())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── token estimation ──────────────────────────────────────────────────────────

def est_tokens(text: str) -> int:
    """Rough token count: len(text) // 4 + 4."""
    if not text:
        return 4
    return len(text) // 4 + 4


# ── ACCUMULATE helpers ────────────────────────────────────────────────────────

def queue_candidate(
    agent_id: str,
    session_id: str,
    candidate_type: str,
    payload: dict,
    confidence: float,
) -> int:
    """Insert a candidate into memory_review_queue; returns candidate_id."""
    sql = """
        INSERT INTO memory_review_queue
            (agent_id, session_id, candidate_type, payload_json, confidence, status)
        VALUES (%s, %s, %s, %s, %s, 'pending')
        RETURNING candidate_id
    """
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                agent_id,
                session_id,
                candidate_type,
                json.dumps(payload),
                confidence,
            ))
            row = cur.fetchone()
            return row[0]


def approve_candidate(candidate_id: int) -> int:
    """
    Approve a review candidate:
      1. Mark it reviewed/approved in memory_review_queue.
      2. Promote the payload into memory_facts as status='approved'.
    Returns the new fact_id.
    """
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Fetch the candidate
            cur.execute(
                "SELECT * FROM memory_review_queue WHERE candidate_id = %s AND status='pending'",
                (candidate_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError(f"No pending candidate with id={candidate_id}")

            payload = row["payload_json"]
            if isinstance(payload, str):
                payload = json.loads(payload)

            # Mark approved in queue
            cur.execute(
                """UPDATE memory_review_queue
                   SET status='approved', reviewed_at=NOW()
                   WHERE candidate_id=%s""",
                (candidate_id,),
            )

            # Promote to memory_facts
            cur.execute(
                """
                INSERT INTO memory_facts
                    (agent_id, user_id, memory_namespace, fact_type,
                     subject, predicate, object_text,
                     confidence, source_session_id, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'approved')
                RETURNING fact_id
                """,
                (
                    row["agent_id"],
                    payload.get("user_id"),
                    payload.get("memory_namespace", "default"),
                    payload.get("fact_type", row["candidate_type"]),
                    payload.get("subject"),
                    payload.get("predicate"),
                    payload.get("object_text"),
                    row["confidence"],
                    row["session_id"],
                ),
            )
            fact_row = cur.fetchone()
            return fact_row["fact_id"]


def reject_candidate(candidate_id: int) -> None:
    """Mark a queue candidate as rejected without touching memory_facts."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE memory_review_queue
                   SET status='rejected', reviewed_at=NOW()
                   WHERE candidate_id=%s AND status='pending'""",
                (candidate_id,),
            )
            if cur.rowcount == 0:
                raise ValueError(f"No pending candidate with id={candidate_id}")


# ── FORGET helpers ────────────────────────────────────────────────────────────

def prune_expired() -> int:
    """
    Set status='expired' on any approved fact whose expires_at < NOW().
    Returns the number of rows pruned.
    """
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE memory_facts
                   SET status='expired', updated_at=NOW()
                   WHERE status='approved'
                     AND expires_at IS NOT NULL
                     AND expires_at < NOW()"""
            )
            return cur.rowcount


# ── RECALL ────────────────────────────────────────────────────────────────────

def recall(namespace: str, token_budget: int) -> tuple[list[dict], list[dict], int]:
    """
    Run the ranked recall query for *namespace*, then greedily include facts
    until *token_budget* is exhausted.

    Returns (included, dropped, tokens_used).
      - included: list of fact dicts that fit in the budget
      - dropped:  list of fact dicts that were left out
      - tokens_used: sum of est_tokens() for included facts
    """
    sql = """
        SELECT fact_id, subject, predicate, object_text, confidence, updated_at
        FROM memory_facts
        WHERE memory_namespace = %s
          AND status = 'approved'
          AND (expires_at IS NULL OR expires_at > NOW())
        ORDER BY confidence DESC NULLS LAST, updated_at DESC
    """
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (namespace,))
            rows = [dict(r) for r in cur.fetchall()]

    included = []
    dropped = []
    tokens_used = 0

    for row in rows:
        text = f"{row['subject']} {row['predicate']} {row['object_text']}"
        cost = est_tokens(text)
        if tokens_used + cost <= token_budget:
            row["_tokens"] = cost
            included.append(row)
            tokens_used += cost
        else:
            row["_tokens"] = cost
            dropped.append(row)

    return included, dropped, tokens_used
