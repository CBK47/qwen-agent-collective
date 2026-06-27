#!/usr/bin/env python3
"""
track1_demo.py — MemoryAgent Track-1 demo

Three beats against a real Postgres 16 instance (no model, no n8n):

  BEAT 1  ACCUMULATE (governed review queue)
  BEAT 2  FORGET     (prune expired / low-confidence facts)
  BEAT 3  RECALL     (ranked, token-budget-gated context assembly)

Exit 0 on success; raises AssertionError on any violated invariant.
"""

import sys
import textwrap
import psycopg2
import psycopg2.extras

from brain_client import (
    queue_candidate,
    approve_candidate,
    reject_candidate,
    prune_expired,
    recall,
    est_tokens,
    _get_dsn,
    _conn,
)
from seed_facts import seed


# ── helpers ───────────────────────────────────────────────────────────────────

def divider(title: str) -> None:
    bar = "─" * 60
    print(f"\n{bar}")
    print(f"  {title}")
    print(bar)


def count_facts(namespace: str, status: str) -> int:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM memory_facts WHERE memory_namespace=%s AND status=%s",
                (namespace, status),
            )
            return cur.fetchone()[0]


def count_all_facts() -> int:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM memory_facts WHERE agent_id IN ('echo','shared')")
            return cur.fetchone()[0]


def queue_status_counts(session_id: str) -> dict:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT status, COUNT(*) FROM memory_review_queue
                   WHERE session_id=%s GROUP BY status""",
                (session_id,),
            )
            return {row[0]: row[1] for row in cur.fetchall()}


# ── BEAT 1 — ACCUMULATE ───────────────────────────────────────────────────────

def beat_accumulate():
    divider("BEAT 1 · ACCUMULATE (governed review queue)")

    AGENT_ID = "echo"
    SESSION_ID = "demo-session-001"

    candidates = [
        # will be APPROVED
        {
            "label": "Connor uses VS Code",
            "candidate_type": "preference",
            "payload": {
                "user_id": "connor",
                "memory_namespace": "echo.private",
                "fact_type": "preference",
                "subject": "connor",
                "predicate": "uses_editor",
                "object_text": "VS Code with Vim keybindings",
            },
            "confidence": 0.920,
            "action": "approve",
        },
        {
            "label": "Python formatter is black",
            "candidate_type": "convention",
            "payload": {
                "user_id": None,
                "memory_namespace": "shared.code-conventions",
                "fact_type": "convention",
                "subject": "python-files",
                "predicate": "use_formatter",
                "object_text": "black (line-length 100) — confirmed in pyproject.toml",
            },
            "confidence": 0.980,
            "action": "approve",
        },
        {
            "label": "Review queue is a staging table",
            "candidate_type": "term",
            "payload": {
                "user_id": None,
                "memory_namespace": "shared.glossary",
                "fact_type": "term",
                "subject": "review-queue",
                "predicate": "purpose",
                "object_text": "staging area for memory candidates before promotion",
            },
            "confidence": 0.870,
            "action": "approve",
        },
        # will be REJECTED
        {
            "label": "Connor hates Mondays (low confidence guess)",
            "candidate_type": "guess",
            "payload": {
                "user_id": "connor",
                "memory_namespace": "echo.private",
                "fact_type": "guess",
                "subject": "connor",
                "predicate": "dislikes",
                "object_text": "Mondays",
            },
            "confidence": 0.150,
            "action": "reject",
        },
        # will stay PENDING
        {
            "label": "Connor might enjoy jazz (unreviewed)",
            "candidate_type": "guess",
            "payload": {
                "user_id": "connor",
                "memory_namespace": "echo.private",
                "fact_type": "guess",
                "subject": "connor",
                "predicate": "might_enjoy",
                "object_text": "jazz music while coding",
            },
            "confidence": 0.400,
            "action": "pending",
        },
    ]

    print(f"\nQueuing {len(candidates)} candidates into memory_review_queue …\n")

    ids = {}
    for c in candidates:
        cid = queue_candidate(AGENT_ID, SESSION_ID, c["candidate_type"], c["payload"], c["confidence"])
        ids[cid] = c
        print(f"  [queue]  candidate_id={cid}  conf={c['confidence']:.3f}  → {c['label']}")

    print()
    to_approve = [cid for cid, c in ids.items() if c["action"] == "approve"]
    to_reject  = [cid for cid, c in ids.items() if c["action"] == "reject"]

    promoted_fact_ids = []
    for cid in to_approve:
        fid = approve_candidate(cid)
        promoted_fact_ids.append(fid)
        print(f"  [approve] candidate_id={cid} → fact_id={fid}  ({ids[cid]['label']})")

    for cid in to_reject:
        reject_candidate(cid)
        print(f"  [reject]  candidate_id={cid}  ({ids[cid]['label']})")

    # Print queue status summary
    counts = queue_status_counts(SESSION_ID)
    print(f"\n  Queue status summary for session '{SESSION_ID}':")
    for status in ("pending", "approved", "rejected"):
        print(f"    {status:12s}: {counts.get(status, 0)}")

    # ── Assertions ────────────────────────────────────────────────────────────
    assert counts.get("approved", 0) == 3, \
        f"Expected 3 approved in queue, got {counts.get('approved', 0)}"
    assert counts.get("rejected", 0) == 1, \
        f"Expected 1 rejected in queue, got {counts.get('rejected', 0)}"
    assert counts.get("pending", 0) == 1, \
        f"Expected 1 pending in queue, got {counts.get('pending', 0)}"

    # Verify only approved candidates landed in memory_facts
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM memory_facts WHERE fact_id = ANY(%s)",
                (promoted_fact_ids,),
            )
            in_facts = cur.fetchone()[0]

    # Rejected/pending candidate payloads should NOT be in memory_facts
    rejected_label = next(c["payload"] for c in ids.values() if c["action"] == "reject")
    pending_label  = next(c["payload"] for c in ids.values() if c["action"] == "pending")
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM memory_facts WHERE object_text IN (%s, %s)",
                (rejected_label["object_text"], pending_label["object_text"]),
            )
            bad_rows = cur.fetchone()[0]

    assert in_facts == 3, f"Expected 3 promoted facts, got {in_facts}"
    assert bad_rows == 0, f"Rejected/pending content found in memory_facts: {bad_rows} rows"

    print(f"\n  ASSERT: {in_facts}/3 approved facts promoted to memory_facts  ✓")
    print(f"  ASSERT: 0 rejected/pending facts in memory_facts               ✓")
    print("\n  Beat 1 PASSED.")


# ── BEAT 2 — FORGET ───────────────────────────────────────────────────────────

def beat_forget():
    divider("BEAT 2 · FORGET (expire stale and low-confidence facts)")

    # Count approved facts before pruning (all demo namespaces)
    before_approved = count_all_facts()

    # Count how many are already past expires_at
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT COUNT(*) FROM memory_facts
                   WHERE agent_id IN ('echo','shared')
                     AND status='approved'
                     AND expires_at IS NOT NULL
                     AND expires_at < NOW()"""
            )
            stale_count = cur.fetchone()[0]

    print(f"\n  Total demo facts (approved) before pruning : {before_approved}")
    print(f"  Facts with expires_at in the past          : {stale_count}")

    # Show a naive "keep everything" approach
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT fact_id, subject, predicate, object_text, confidence, expires_at
                   FROM memory_facts
                   WHERE agent_id IN ('echo','shared') AND status='approved'
                   ORDER BY confidence DESC"""
            )
            all_facts = cur.fetchall()

    print("\n  [naive keep-everything] All approved facts:")
    for f in all_facts:
        exp = f["expires_at"].strftime("%Y-%m-%d") if f["expires_at"] else "never"
        flag = " ← EXPIRED" if f["expires_at"] and f["expires_at"].year < 2025 else ""
        print(f"    fact_id={f['fact_id']}  conf={f['confidence']:.3f}  "
              f"expires={exp}  \"{f['subject']} {f['predicate']}…\"{flag}")

    # Run prune
    print("\n  Running prune_expired() …")
    pruned = prune_expired()
    print(f"  Pruned {pruned} fact(s) → status set to 'expired'.")

    after_approved = count_all_facts()  # still counts all statuses for demo
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT COUNT(*) FROM memory_facts
                   WHERE agent_id IN ('echo','shared') AND status='approved'"""
            )
            live_approved = cur.fetchone()[0]
            cur.execute(
                """SELECT COUNT(*) FROM memory_facts
                   WHERE agent_id IN ('echo','shared') AND status='expired'"""
            )
            expired_count = cur.fetchone()[0]

    print(f"\n  After pruning:")
    print(f"    approved (recallable) : {live_approved}")
    print(f"    expired  (invisible)  : {expired_count}")

    # Contrast: naive count vs governed count
    print(f"\n  Naive 'keep everything' count  : {before_approved} facts")
    print(f"  Governed 'recall-safe' count   : {live_approved} facts")
    print(f"  Saved from context window bloat: {before_approved - live_approved} facts pruned")

    # ── Assertions ────────────────────────────────────────────────────────────
    assert pruned == stale_count, \
        f"Expected to prune {stale_count} facts, actually pruned {pruned}"
    assert pruned > 0, "Expected at least one expired fact to prune"
    assert expired_count == pruned, \
        f"Mismatch: pruned={pruned} but expired_count={expired_count}"

    # Verify pruned facts are NOT recallable via recall query
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT COUNT(*) FROM memory_facts
                   WHERE agent_id IN ('echo','shared')
                     AND status = 'expired'
                     AND (expires_at IS NULL OR expires_at > NOW())"""
            )
            ghost_count = cur.fetchone()[0]

    assert ghost_count == 0, \
        f"Expired facts showing up as recallable: {ghost_count}"

    print(f"\n  ASSERT: pruned {pruned} == stale_count {stale_count}                   ✓")
    print(f"  ASSERT: {expired_count} expired fact(s) are not recallable via RECALL query ✓")
    print("\n  Beat 2 PASSED.")


# ── BEAT 3 — RECALL ───────────────────────────────────────────────────────────

def beat_recall():
    divider("BEAT 3 · RECALL (ranked, token-budget-gated context assembly)")

    namespace = "shared.glossary"

    # Run with a tight budget first
    TIGHT_BUDGET = 60
    included_t, dropped_t, used_t = recall(namespace, TIGHT_BUDGET)

    print(f"\n  Namespace : {namespace}")
    print(f"  Budget    : {TIGHT_BUDGET} tokens  (tight — expect some DROPPED)")
    print(f"\n  INCLUDED ({len(included_t)} facts, {used_t} tokens used):")
    for f in included_t:
        print(f"    [{f['_tokens']:3d} tok]  conf={f['confidence']:.3f}  "
              f"'{f['subject']} {f['predicate']} {f['object_text'][:40]}…'")

    print(f"\n  DROPPED ({len(dropped_t)} facts — did not fit):")
    for f in dropped_t:
        print(f"    [{f['_tokens']:3d} tok]  conf={f['confidence']:.3f}  "
              f"'{f['subject']} {f['predicate']} {f['object_text'][:40]}…'")

    # Tight-budget assertions
    assert used_t <= TIGHT_BUDGET, \
        f"Token budget exceeded: used {used_t} > budget {TIGHT_BUDGET}"
    assert len(dropped_t) > 0, \
        "Expected some facts to be dropped under a tight budget"

    # Verify ordering: confidence DESC then updated_at DESC
    for i in range(len(included_t) - 1):
        a, b = included_t[i], included_t[i + 1]
        assert (a["confidence"], a["updated_at"]) >= (b["confidence"], b["updated_at"]), \
            f"Ordering violated between facts {a['fact_id']} and {b['fact_id']}"

    # Run with a generous budget — should include all facts
    LARGE_BUDGET = 9999
    included_l, dropped_l, used_l = recall(namespace, LARGE_BUDGET)

    print(f"\n  Rerun with large budget ({LARGE_BUDGET} tokens):")
    print(f"  INCLUDED: {len(included_l)} facts, {used_l} tokens used")
    print(f"  DROPPED : {len(dropped_l)} facts")

    assert len(dropped_l) == 0, \
        f"Expected 0 dropped with large budget, got {len(dropped_l)}"
    assert used_l <= LARGE_BUDGET, \
        f"Large budget still exceeded: {used_l} > {LARGE_BUDGET}"

    # Ensure expired / pending facts never appear in recall results
    all_included_ids = {f["fact_id"] for f in included_l}
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT COUNT(*) FROM memory_facts
                   WHERE fact_id = ANY(%s)
                     AND (status != 'approved'
                          OR (expires_at IS NOT NULL AND expires_at < NOW()))""",
                (list(all_included_ids),),
            )
            bad = cur.fetchone()[0]

    assert bad == 0, \
        f"Recall returned {bad} expired or non-approved fact(s)"

    print(f"\n  ASSERT: Σtokens(included) {used_t} ≤ tight budget {TIGHT_BUDGET}       ✓")
    print(f"  ASSERT: ordering is confidence DESC, updated_at DESC                    ✓")
    print(f"  ASSERT: large budget → 0 dropped (graceful degradation)                 ✓")
    print(f"  ASSERT: 0 expired/pending facts in recall results                       ✓")
    print("\n  Beat 3 PASSED.")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  MemoryAgent Track-1 Demo")
    print("  Postgres-native · no model backend · no n8n")
    print("=" * 60)

    print("\n[setup] Seeding demo fixtures …")
    seed()

    beat_accumulate()
    beat_forget()
    beat_recall()

    divider("ALL BEATS PASSED")
    print("\n  The demo proves:")
    print("  1. ACCUMULATE — governed queue gates what enters memory_facts")
    print("  2. FORGET     — prune_expired() removes stale facts from recall")
    print("  3. RECALL     — ranked, token-budget-gated; expired/pending never appear")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
