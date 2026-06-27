# brain — keystone plan (P0, unblocks all 5 tracks)

**Owner:** chat:brain · **Priority:** P0 — single dependency under T2–T5.
Per `HACKATHON.md` SSOT, this is the highest-leverage remaining work.

## Keystone — `shared/brain.py`
- [ ] Build `shared/brain.py` exposing `ingest(...)` + `retrieve(...)` over Postgres + Qdrant, using the running brain stack (`echo-postgres`, `echo-qdrant`) and the committed schema (`brain/db/postgres-init.sql`).
- [ ] Prove ingest → retrieve end to end locally with memory-echo (the Track-1 path).
- [ ] Freeze the brain client API so all five agents import it (never fork).

## Cross-cutting submission proofs (required ×5)
- [ ] One shared Alibaba Cloud deploy harness every track reuses (not 5 bespoke deploys).
- [ ] Fill the per-track deploy-proof links in `HACKATHON.md` (currently 5× "link tbd").
- [ ] Record per-track 60–90s demo videos.

> NOTE: the keystone, deploys, and videos are P0 and best built deliberately —
> not left to the flaky autonomous local loop. The loop is for small code/doc
> increments and front-end scaffolding, not the keystone or the human-only proofs.
