# brain — keystone plan (P0, unblocks all 5 tracks)

**Owner:** chat:brain · **Priority:** P0 — single dependency under T2–T5.
Per `HACKATHON.md` SSOT, this is the highest-leverage remaining work.

## Keystone — `shared/brain.py`
- [x] Build `shared/brain.py` exposing `ingest(...)` + `retrieve(...)` over Postgres + Qdrant, using the running brain stack (`echo-postgres`, `echo-qdrant`) and the committed schema (`brain/db/postgres-init.sql`).
- [x] Prove ingest → retrieve end to end locally (DashScope `text-embedding-v3` → Qdrant cosine search; governance by status + `expires_at`; token-budget truncation). Run `python -m shared.brain`.
- [x] Freeze the brain client API so all five agents import it (`Brain`, `ingest`, `retrieve`, `recent_events`).

> Provisioned: an isolated `brain` DB + `brain_user` role inside the running Postgres
> instance (no port conflict with Local Echo), schema applied from `postgres-init.sql`.
> Qdrant collections are created per namespace on first ingest (dim 1024, cosine).

## Cross-cutting submission proofs (required ×5)
- [ ] One shared Alibaba Cloud deploy harness every track reuses (not 5 bespoke deploys).
- [ ] Fill the per-track deploy-proof links in `HACKATHON.md` (currently 5× "link tbd").
- [ ] Record per-track 60–90s demo videos.

> NOTE: the keystone, deploys, and videos are P0 and best built deliberately —
> not left to the flaky autonomous local loop. The loop is for small code/doc
> increments and front-end scaffolding, not the keystone or the human-only proofs.
