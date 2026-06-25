# Orchestrator Port Plan — Ollama → Qwen on DashScope

**Status:** plan only (no JSON authored this pass). The original 20 KB
`n8n-memory-orchestrator.json` lives in `CBK47/Agents` and was **not reachable**
from the web session that wrote this file. Build the workflow on your Mac, where
you can copy the real JSON and apply the port below.

The brain orchestrator is a single n8n workflow exposing **one webhook API** with
three actions: `retrieve`, `ingest`, `manifest`. The port = repoint the three model
nodes from local Ollama to **Qwen on Alibaba Cloud Model Studio (DashScope,
OpenAI-compatible)**, fully parameterized via `$env`. No hardcoded hosts/models.

## The three nodes to port

| Node | Was (Ollama) | Becomes (DashScope, OpenAI-compatible) |
|---|---|---|
| **Embed Query** | local `/api/embeddings` | `POST {{$env.DASHSCOPE_BASE_URL}}/embeddings`, model `{{$env.QWEN_EMBED_MODEL}}` (`text-embedding-v3`) |
| **Embed Summary** | local `/api/embeddings` | `POST {{$env.DASHSCOPE_BASE_URL}}/embeddings`, model `{{$env.QWEN_EMBED_MODEL}}` |
| **Summarise & Extract** | local `/api/generate` | `POST {{$env.DASHSCOPE_BASE_URL}}/chat/completions`, model `{{$env.QWEN_CHAT_MODEL}}` (`qwen-plus`) |

Common HTTP Request node settings for all three:
- Header `Authorization: Bearer {{$env.DASHSCOPE_API_KEY}}`
- Header `Content-Type: application/json`
- Embeddings body: `{ "model": "{{$env.QWEN_EMBED_MODEL}}", "input": "<text>" }`
  → read vector from `data[0].embedding` (length **1024**, matches Qdrant collections).
- Chat body: `{ "model": "{{$env.QWEN_CHAT_MODEL}}", "messages": [...], "temperature": 0.2 }`
  → read text from `choices[0].message.content`.

> Gotcha: DashScope embeddings accept a single string or an array under `input`.
> Keep batch size modest; map the response back by index if you batch.

## The three actions (node-graph intent)

**Webhook (entry)** → **Switch on `action`** → one of:

- **`manifest(agent)`** → return that agent's collections / namespaces / exports
  (read straight from `memory-manifest.yaml` semantics). No model call.

- **`retrieve(agent, session_id, query, [namespace|tags])`**
  1. Postgres: fetch `memory_facts` where `status='approved'` **and**
     (`expires_at IS NULL OR expires_at > NOW()`) for the agent's namespace.
  2. **Embed Query** (DashScope) → vector.
  3. Qdrant: search the agent's collection(s) with that vector.
  4. Rank (vector score + confidence/recency) and **truncate to a context budget**.
  5. Return the combined context bundle.

- **`ingest(agent, session_id, messages, [source_type], [source_path])`**
  1. Normalise transcript.
  2. **Summarise & Extract** (DashScope qwen-plus) → session summary + candidate facts.
  3. Postgres: store session summary; write candidates to `memory_review_queue`
     (`status='pending'`).
  4. **Embed Summary** (DashScope) → upsert point to Qdrant.
  5. Return an ingest receipt.

## Supporting stack (for your Mac)
- `docker-compose.yml`: `postgres` (auto-runs `db/postgres-init.sql`), `qdrant`, `n8n`,
  all wired from `.env`.
- Create Qdrant collections per `memory-manifest.yaml` (dim 1024, cosine).
- Import the workflow into n8n; set the `DASHSCOPE_*` / `QWEN_*` / `POSTGRES_*` /
  `QDRANT_*` env vars on the n8n container.

## Mac kickoff checklist
- [ ] Copy the real `n8n-memory-orchestrator.json` from `CBK47/Agents@claude/qwen-hackathon-ideas-bs1z60:/brain/orchestrator/`.
- [ ] Apply the 3-node port table above; remove any Ollama host references.
- [ ] `cp brain/.env.example brain/.env` and fill `DASHSCOPE_API_KEY`.
- [ ] `docker compose up`; confirm Postgres init + Qdrant + n8n are healthy.
- [ ] Create Qdrant collections (dim 1024).
- [ ] Smoke test: `manifest` → `ingest` → `retrieve` (see Track-1 demo harness, deferred).
- [ ] Capture a real DashScope response as deployment proof.
