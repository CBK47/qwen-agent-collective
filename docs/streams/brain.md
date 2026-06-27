# Stream: Brain (shared memory substrate)

- **Track:** 1 (MemoryAgent) — and the dependency for all five agents
- **Tier:** core (build first)
- **Goal:** one Postgres + Qdrant + n8n memory service on Alibaba Cloud that every
  agent reads/writes under namespace + review-queue governance.
- **Why Qwen:** the orchestrator calls Qwen on DashScope for `Summarise & Extract`
  (`qwen-plus`) and embeddings (`text-embedding-v3`).
- **Brain namespace:** it *is* the substrate — hosts `<agent>.private` + `shared.*`.

## Current state
- `brain/db/postgres-init.sql` — full schema (agents, users, sessions, messages,
  memory_facts, memory_events, memory_review_queue, projects, people, devices,
  source_registry, retrieval_feedback) + indexes + seed (echo, skippy, shared).
- `brain/orchestrator/n8n-memory-orchestrator.json` — 41-node workflow with
  `retrieve` / `ingest` / `manifest` actions. **Still calls local Ollama** at 3 nodes.
- `brain/memory-manifest.yaml` — echo + skippy namespaces, qdrant collections.
- `brain/local-echo.env.example` — old Ollama env (reference).

## MVP bar
Brain runs on Alibaba Cloud; `manifest` → `ingest` → `retrieve` work end-to-end with
Qwen on DashScope; at least the 5 agents + shared namespaces are seeded.

## Next steps (execute in order)
1. **DashScope port** — repoint the 3 Ollama nodes in the orchestrator JSON:
   `Embed Query` (embeddinggemma→`text-embedding-v3`), `Summarise & Extract`
   (gpt-oss→`qwen-plus`), `Embed Summary` (embeddinggemma→`text-embedding-v3`). Use
   the DashScope OpenAI-compatible endpoint + bearer `DASHSCOPE_API_KEY`; parameterise
   via env (no hardcoded hosts/models).
2. **Seed all five agents + shared namespaces** in `postgres-init.sql`: add
   `git-committer`, `open-translate`, `showrunner`; document `shared.code-conventions`
   and `shared.glossary`.
3. **Qdrant bootstrap** — script/workflow to create `<agent>_private` + `shared_*`
   collections at embedding dim 1024 (matches `text-embedding-v3`).
4. **Deploy on Alibaba Cloud** (ECS or Function Compute) — Postgres + Qdrant + n8n;
   save a deployment-proof file (real config calling Alibaba Cloud + running evidence).
5. **Smoke test** — `manifest` then `ingest` (a tiny transcript) then `retrieve`;
   confirm rows in Postgres + points in Qdrant.
6. Architecture diagram (`docs/architecture/`), `HACKATHON.md` log.

## Dependencies
None — this unblocks everything else. Do the DashScope port before any agent relies on
live recall.

## Definition of done
- [ ] Orchestrator calls Qwen on DashScope only (no Ollama in the judged path)
- [ ] 5 agents + shared namespaces seeded; Qdrant collections exist
- [ ] Deployed on Alibaba Cloud + proof file
- [ ] `manifest`/`ingest`/`retrieve` verified end-to-end
- [ ] Diagram + `HACKATHON.md`
