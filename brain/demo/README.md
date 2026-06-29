# MemoryAgent Track-1 Demo

A self-contained, narrated proof-of-concept for three core MemoryAgent beats —
**Accumulate**, **Forget**, and **Recall** — running against a real Postgres 16
instance with no model backend and no n8n.

## One-command run

```bash
cd brain/demo
bash run.sh
```

This script:
1. Starts Postgres 16 via `docker compose` (mounts the real schema from `../db/postgres-init.sql`)
2. Waits for the healthcheck to pass
3. `pip install`s `psycopg2-binary`
4. Seeds idempotent fixtures (`seed_facts.py`)
5. Runs `track1_demo.py` (exits 0 on success)

To tear down afterwards:

```bash
docker compose -f brain/demo/docker-compose.demo.yml down -v
```

---

## What each beat proves

### Beat 1 — ACCUMULATE (governed review queue)
- Five candidates are queued into `memory_review_queue` with `status='pending'`.
- Three are **approved** → promoted into `memory_facts` with `status='approved'`.
- One is **rejected** → stays in the queue as `status='rejected'`, never reaches `memory_facts`.
- One remains **pending** → unreviewed, never reaches `memory_facts`.
- Assertions verify that exactly 3 facts land in `memory_facts` and that rejected / pending content is absent.

**Proves**: The governed queue is the only gate into long-term memory.

### Beat 2 — FORGET (prune expired / stale facts)
- The seed data includes facts with `expires_at` in the past (e.g. 2020, 2021, 2022).
- `prune_expired()` runs `UPDATE memory_facts SET status='expired' WHERE expires_at < NOW()`.
- Before/after counts are printed, contrasting the naïve "keep everything" total against the governed recall-safe total.
- Assertions confirm that pruned facts are no longer recallable via the `RECALL` query (`status='approved' AND (expires_at IS NULL OR expires_at > NOW())`).

**Proves**: Memory doesn't grow unbounded; stale facts are invisible to agents.

### Beat 3 — RECALL (ranked, token-budget-gated context assembly)
- Runs the canonical ranked query:
  `ORDER BY confidence DESC NULLS LAST, updated_at DESC`
- Greedily includes facts until a **tight token budget** (60 tokens) is hit; prints `INCLUDED` vs `DROPPED` with per-fact token costs and a running tally.
- Re-runs with a **large budget** (9999 tokens) to show graceful degradation (0 dropped).
- Assertions:
  - `Σtokens(included) ≤ budget`
  - Ordering is confidence-then-recency ranked
  - Expired and pending facts never appear in results

**Proves**: Context assembly is deterministic, budget-safe, and quality-ranked.

---

## Running Individual Scripts

### Environment Setup

Before running any scripts, ensure the Postgres database is running and environment variables are set.

Start the Postgres container:

```bash
cd brain/demo
docker compose -f docker-compose.demo.yml up -d
```

Wait for the database to be ready:

```bash
docker compose -f docker-compose.demo.yml wait
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Set environment variables:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=collective
export POSTGRES_USER=collective
export POSTGRES_PASSWORD=change-me
```

### seed_facts.py

Seed the database with initial facts:

```bash
python seed_facts.py
```

This script is idempotent and can be run multiple times.

### ingest_glossary.py

Ingest a glossary file into the database. Example:

```bash
python ingest_glossary.py --file sample_glossary.txt
```

Sample `sample_glossary.txt` content:

```
AI: Artificial Intelligence
ML: Machine Learning
NLP: Natural Language Processing
```

### track1_demo.py

Run the full demo after seeding the database:

```bash
python track1_demo.py
```

This script will execute the three beats (Accumulate, Forget, Recall) with detailed logging and assertions.

---

## File layout

```
brain/demo/
├── docker-compose.demo.yml   Postgres 16 + healthcheck
├── requirements.txt          psycopg2-binary
├── brain_client.py           queue/approve/reject/prune/recall helpers
├── seed_facts.py             idempotent fixtures (15 facts, varied confidence/expiry)
├── ingest_glossary.py        glossary ingestion script
├── track1_demo.py            narrated run with assertions (exit 0 on success)
├── run.sh                    one-command launcher
└── README.md                 this file
```

## Environment variables

| Variable          | Default      | Description           |
|-------------------|--------------|-----------------------|
| `POSTGRES_HOST`   | `localhost`  | Postgres host         |
| `POSTGRES_PORT`   | `5432`       | Postgres port         |
| `POSTGRES_DB`     | `collective` | Database name         |
| `POSTGRES_USER`   | `collective` | Database user         |
| `POSTGRES_PASSWORD` | `change-me` | Database password    |
