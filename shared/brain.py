"""Shared brain client — the keystone all five agents build on.

Two operations over the shared memory stores:

  - ``ingest()``   : persist a memory fact in Postgres (structured + governance)
                     and its embedding in Qdrant (semantic recall).
  - ``retrieve()`` : embed a query, semantically search a namespace, apply
                     governance (status + expiry), and return ranked facts
                     truncated to an optional token budget.

Structured store : Postgres ``memory_facts`` (see ``brain/db/postgres-init.sql``).
Semantic store   : Qdrant, one collection per memory namespace.
Embeddings       : ``shared.dashscope.embed`` (DashScope ``text-embedding-v3``).

Agents import this module; they never talk to Postgres/Qdrant directly. Keep the
public surface (``Brain``, ``ingest``, ``retrieve``) stable — it is frozen API.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

from shared.dashscope import embed as dashscope_embed

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv()

LOGGER = logging.getLogger("qwen_collective.brain")

DEFAULT_EMBED_DIM = int(os.getenv("BRAIN_EMBED_DIM", "1024"))  # text-embedding-v3


class BrainError(RuntimeError):
    """Raised when a brain operation cannot be completed."""


def _est_tokens(text: str) -> int:
    """Cheap token estimate (~4 chars/token) for budget-bounded recall."""
    return max(1, len(text) // 4)


def _collection_for(namespace: str) -> str:
    """Map a memory namespace (``echo.private``) to a Qdrant collection name."""
    return namespace.strip().replace(".", "_").replace("-", "_").lower()


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class BrainConfig:
    """Connection settings, loaded from the environment."""

    pg_host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    pg_port: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    pg_db: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "brain"))
    pg_user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "brain_user"))
    pg_password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", "changeme"))
    qdrant_host: str = field(default_factory=lambda: os.getenv("QDRANT_HOST", "localhost"))
    qdrant_port: int = field(default_factory=lambda: int(os.getenv("QDRANT_PORT", "6333")))
    qdrant_api_key: str | None = field(default_factory=lambda: os.getenv("QDRANT_API_KEY") or None)
    embed_dim: int = DEFAULT_EMBED_DIM


@dataclass
class Memory:
    """A retrieved memory fact with its semantic relevance score."""

    fact_id: int
    text: str
    score: float
    namespace: str
    agent_id: str
    fact_type: str
    expires_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "text": self.text,
            "score": round(self.score, 4),
            "namespace": self.namespace,
            "agent_id": self.agent_id,
            "fact_type": self.fact_type,
            "expires_at": self.expires_at,
        }


class Brain:
    """Client over the shared memory stores (Postgres + Qdrant)."""

    def __init__(self, config: BrainConfig | None = None) -> None:
        self.config = config or BrainConfig()
        self._pg: psycopg2.extensions.connection | None = None
        self._qdrant: QdrantClient | None = None

    # ── connections (lazy) ────────────────────────────────────────────────────
    @property
    def pg(self) -> psycopg2.extensions.connection:
        if self._pg is None or self._pg.closed:
            try:
                self._pg = psycopg2.connect(
                    host=self.config.pg_host, port=self.config.pg_port,
                    dbname=self.config.pg_db, user=self.config.pg_user,
                    password=self.config.pg_password,
                )
            except psycopg2.Error as exc:
                raise BrainError(f"Postgres connection failed: {exc}") from exc
        return self._pg

    @property
    def qdrant(self) -> QdrantClient:
        if self._qdrant is None:
            self._qdrant = QdrantClient(
                host=self.config.qdrant_host, port=self.config.qdrant_port,
                api_key=self.config.qdrant_api_key,
            )
        return self._qdrant

    def _ensure_collection(self, name: str) -> None:
        """Create the Qdrant collection on first use (idempotent)."""
        if not self.qdrant.collection_exists(name):
            self.qdrant.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=self.config.embed_dim, distance=Distance.COSINE),
            )
            LOGGER.info("created Qdrant collection %s", name)

    @staticmethod
    def _as_vector(embedding: Any) -> list[float]:
        """Normalise dashscope.embed output (single string) to a flat vector."""
        if embedding and isinstance(embedding[0], list):
            return embedding[0]
        return embedding

    # ── ingest ────────────────────────────────────────────────────────────────
    def ingest(
        self,
        *,
        agent_id: str,
        namespace: str,
        text: str,
        fact_type: str = "note",
        user_id: str | None = None,
        subject: str | None = None,
        predicate: str | None = None,
        confidence: float | None = None,
        status: str = "approved",
        expires_at: datetime | None = None,
        source_session_id: str | None = None,
    ) -> int:
        """Persist a memory fact and its embedding; return the new ``fact_id``.

        The fact row lands in Postgres ``memory_facts`` (the governance record);
        the embedding lands in the namespace's Qdrant collection for recall.
        """
        if not text or not text.strip():
            raise BrainError("ingest() requires non-empty text")

        with self.pg.cursor() as cur:
            cur.execute(
                """
                INSERT INTO memory_facts
                  (agent_id, user_id, memory_namespace, fact_type, subject,
                   predicate, object_text, confidence, status, source_session_id, expires_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING fact_id
                """,
                (agent_id, user_id, namespace, fact_type, subject, predicate,
                 text, confidence, status, source_session_id, expires_at),
            )
            fact_id = cur.fetchone()[0]
        self.pg.commit()

        vector = self._as_vector(dashscope_embed(text))
        collection = _collection_for(namespace)
        self._ensure_collection(collection)
        self.qdrant.upsert(
            collection_name=collection,
            points=[PointStruct(
                id=fact_id,
                vector=vector,
                payload={
                    "fact_id": fact_id,
                    "agent_id": agent_id,
                    "namespace": namespace,
                    "fact_type": fact_type,
                    "text": text,
                    "status": status,
                    "expires_at": expires_at.isoformat() if expires_at else None,
                },
            )],
        )
        LOGGER.info("ingested fact %s into %s", fact_id, namespace)
        return fact_id

    # ── retrieve ──────────────────────────────────────────────────────────────
    def retrieve(
        self,
        query: str,
        *,
        namespace: str,
        top_k: int = 10,
        token_budget: int | None = None,
        status: str | None = "approved",
        include_expired: bool = False,
    ) -> list[Memory]:
        """Semantic recall over a namespace, governed and budget-bounded.

        Embeds ``query``, searches the namespace collection, drops facts that are
        not ``status`` or are past ``expires_at`` (unless ``include_expired``),
        and truncates the ranked results so their estimated tokens stay within
        ``token_budget`` (if given).
        """
        if not query or not query.strip():
            raise BrainError("retrieve() requires a non-empty query")

        collection = _collection_for(namespace)
        if not self.qdrant.collection_exists(collection):
            return []

        vector = self._as_vector(dashscope_embed(query))
        query_filter = None
        if status:
            query_filter = Filter(must=[FieldCondition(key="status", match=MatchValue(value=status))])

        hits = self.qdrant.query_points(
            collection_name=collection,
            query=vector,
            query_filter=query_filter,
            limit=max(top_k * 2, top_k),  # over-fetch to survive expiry filtering
            with_payload=True,
        ).points

        now = _now()
        results: list[Memory] = []
        spent = 0
        for hit in hits:
            payload = hit.payload or {}
            exp = payload.get("expires_at")
            if exp and not include_expired:
                try:
                    if datetime.fromisoformat(exp) <= now:
                        continue
                except ValueError:
                    pass
            text = payload.get("text", "")
            if token_budget is not None:
                cost = _est_tokens(text)
                if spent + cost > token_budget and results:
                    break
                spent += cost
            results.append(Memory(
                fact_id=int(payload.get("fact_id", hit.id)),
                text=text,
                score=float(hit.score),
                namespace=payload.get("namespace", namespace),
                agent_id=payload.get("agent_id", ""),
                fact_type=payload.get("fact_type", "note"),
                expires_at=exp,
            ))
            if len(results) >= top_k:
                break
        return results

    # ── events (showrunner reads these) ───────────────────────────────────────
    def recent_events(self, *, agent_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        """Return recent ``memory_events`` rows (newest first), for dramatization."""
        with self.pg.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if agent_id:
                cur.execute(
                    "SELECT * FROM memory_events WHERE agent_id=%s "
                    "ORDER BY COALESCE(event_time, created_at) DESC LIMIT %s",
                    (agent_id, limit),
                )
            else:
                cur.execute(
                    "SELECT * FROM memory_events "
                    "ORDER BY COALESCE(event_time, created_at) DESC LIMIT %s",
                    (limit,),
                )
            return [dict(r) for r in cur.fetchall()]

    def close(self) -> None:
        if self._pg and not self._pg.closed:
            self._pg.close()


# ── module-level convenience (singleton), mirroring shared.dashscope ──────────
_DEFAULT: Brain | None = None


def _default() -> Brain:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = Brain()
    return _DEFAULT


def ingest(**kwargs: Any) -> int:
    """Ingest a memory fact via the default brain client. See ``Brain.ingest``."""
    return _default().ingest(**kwargs)


def retrieve(query: str, **kwargs: Any) -> list[Memory]:
    """Retrieve memories via the default brain client. See ``Brain.retrieve``."""
    return _default().retrieve(query, **kwargs)


def _selftest() -> None:
    """Idempotent end-to-end proof: ingest a few facts, recall under a budget.

    Uses a dedicated throwaway namespace and clears both stores first/after so it
    can be re-run cleanly and never pollutes real agent memory.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ns = "selftest.demo"
    collection = _collection_for(ns)
    brain = Brain()
    # clean slate
    if brain.qdrant.collection_exists(collection):
        brain.qdrant.delete_collection(collection)
    with brain.pg.cursor() as cur:
        cur.execute("DELETE FROM memory_facts WHERE memory_namespace=%s", (ns,))
    brain.pg.commit()

    facts = [
        "Connor prefers local-first AI on the DGX Spark over cloud where possible.",
        "The hackathon submission deadline is 2026-07-08, with five tracks.",
        "Skippy is the home-ops agent; Echo is the primary collaboration agent.",
    ]
    ids = [brain.ingest(agent_id="echo", namespace=ns, text=f, fact_type="fact") for f in facts]
    print(f"\ningested fact_ids={ids}")
    hits = brain.retrieve("When is the hackathon due?", namespace=ns, top_k=3, token_budget=40)
    print(f"recall under 40-token budget -> {len(hits)} memory(ies):")
    for m in hits:
        print(f"  [{m.score:.3f}] {m.text}")
    assert hits and "deadline" in hits[0].text, "expected the deadline fact ranked first"
    print("\n✓ brain keystone self-test passed")
    brain.close()


if __name__ == "__main__":
    _selftest()
