# DGX setup runbook — stand up the brain

A Claude agent on the DGX (Ubuntu, Docker up) works through this top-to-bottom to
take the brain from "code in a branch" to "running stack + verified end-to-end."
Each phase has **commands** and a **pass bar**. Stop and report if a pass bar fails.

- Repo path (from `run_health_check.sh`): `/home/cbk/qwen-agent-collective` — confirm first.
- Branch: `port-brain-from-agents`.
- Full-stack compose: `brain/docker-compose.yml` (Postgres + Qdrant + n8n) — provided
  but **untested on hardware**; verify healthchecks/ports as you go.
- Phase 1 detail also lives in `brain/demo/DGX-VERIFY.md`.

---

## Phase 0 — Preflight

```bash
cd /home/cbk/qwen-agent-collective || git clone https://github.com/CBK47/qwen-agent-collective.git && cd qwen-agent-collective
git fetch origin && git checkout port-brain-from-agents && git pull
docker info >/dev/null && echo "docker OK"
cp -n brain/.env.example brain/.env          # then put the real DASHSCOPE_API_KEY in brain/.env
```

Test the DashScope key (Singapore intl endpoint, OpenAI-compatible):
```bash
set -a; . brain/.env; set +a
curl -s -o /dev/null -w "chat %{http_code}\n" -X POST "$DASHSCOPE_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY" -H 'Content-Type: application/json' \
  -d '{"model":"qwen-plus","messages":[{"role":"user","content":"ping"}],"max_tokens":5}'
curl -s -o /dev/null -w "embed %{http_code}\n" -X POST "$DASHSCOPE_BASE_URL/embeddings" \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY" -H 'Content-Type: application/json' \
  -d '{"model":"text-embedding-v3","input":"ping"}'
```

**Pass bar:** repo on the branch; `docker OK`; both curls return `200`. (If `400/401`,
the key/region is wrong — see the Qwen/DashScope setup memory: Singapore workspace key.)

---

## Phase 1 — Track-1 demo (proves schema + governance, no stack needed)

```bash
cd brain/demo && bash run.sh
```
**Pass bar:** exits 0; output shows `Beat 1/2/3 PASSED` and `ALL BEATS PASSED`.
Tear down when done: `docker compose -f docker-compose.demo.yml down -v`. Then `cd ../..`.

---

## Phase 2 — Bring up the full stack

> Stop the Phase-1 demo Postgres first (it also binds 5432). Check for port clashes
> on 5432/6333/5678 (`ss -ltnp | grep -E '5432|6333|5678'`); the DGX may already run
> Ollama/other services.

```bash
docker compose -f brain/docker-compose.yml --env-file brain/.env up -d
# wait for Postgres health
until docker inspect --format='{{.State.Health.Status}}' brain_postgres | grep -q healthy; do sleep 2; done
echo "postgres healthy"
curl -s -o /dev/null -w "qdrant %{http_code}\n" http://localhost:6333/healthz
curl -s -o /dev/null -w "n8n %{http_code}\n"   http://localhost:5678/
```

**Pass bar:** `brain_postgres` healthy; qdrant `200`; n8n `200` (first hit may redirect
to setup — fine). On first n8n load, create the owner account in the UI.

---

## Phase 3 — Seed the gaps

### 3a. Add the three missing agents (seed only has echo/skippy/shared)
```bash
docker exec -i brain_postgres psql -U collective -d collective <<'SQL'
INSERT INTO agents (agent_id, agent_slug, display_name, description, system_prompt_path, retrieval_prompt_path) VALUES
  ('git-committer','git-committer','GIT-Committer','Multi-agent PR reviewer','prompts/git-committer/system.md','prompts/git-committer/retrieval.md'),
  ('open-translate','open-translate','Open-Translate','Localization autopilot','prompts/open-translate/system.md','prompts/open-translate/retrieval.md'),
  ('showrunner','showrunner','Showrunner','Society narrator / recaps','prompts/showrunner/system.md','prompts/showrunner/retrieval.md')
ON CONFLICT (agent_id) DO NOTHING;
SELECT agent_id FROM agents ORDER BY agent_id;
SQL
```
**Pass bar:** the SELECT lists all 6 (echo, git-committer, open-translate, shared, showrunner, skippy).

### 3b. Bootstrap Qdrant collections (dim 1024 = text-embedding-v3)
```bash
for c in echo_private skippy_private git-committer_private open-translate_private showrunner_private shared; do
  curl -s -o /dev/null -w "$c %{http_code}\n" -X PUT "http://localhost:6333/collections/$c" \
    -H 'Content-Type: application/json' \
    -d '{"vectors":{"size":1024,"distance":"Cosine"}}'
done
curl -s http://localhost:6333/collections | python3 -m json.tool
```
**Pass bar:** each PUT `200`; collections list shows all six.

---

## Phase 4 — Wire n8n

### 4a. Import workflows (orchestrator + the four new ones)
```bash
for f in brain/orchestrator/n8n-memory-orchestrator.json brain/orchestrator/workflows/*.json; do
  docker exec -i brain_n8n n8n import:workflow --input=- < "$f" && echo "imported $f"
done
```
*(If `--input=-` stdin isn't supported on the image's n8n version, `docker cp` the files
into the container and pass a path.)*

### 4b. Create the Postgres credential (one-time, n8n UI)
In n8n → Credentials → New → Postgres: host `postgres`, port `5432`, db `collective`,
user `collective`, password from `brain/.env`. Open each imported workflow's Postgres
node(s) and select this credential (they ship as `id: REPLACE_ME`). DashScope/QWEN env
is already injected by compose — no credential needed for the HTTP calls.

### 4c. Port the orchestrator's 3 Ollama nodes → DashScope  (brain.md step 1)
Edit `n8n-memory-orchestrator.json` (or the imported copy) at these nodes:

| Node | Was (Ollama) | Change to (DashScope) |
|------|--------------|------------------------|
| `Summarise & Extract` | `/v1/chat/completions`, `gpt-oss` | url `{{$env.DASHSCOPE_BASE_URL}}/chat/completions`, model `{{$env.QWEN_CHAT_MODEL}}`, add header `Authorization: Bearer {{$env.DASHSCOPE_API_KEY}}` |
| `Embed Query` | `/api/embed`, `embeddinggemma` | url `{{$env.DASHSCOPE_BASE_URL}}/embeddings`, body `{model:$env.QWEN_EMBED_MODEL, input:$json.query}`, same auth header |
| `Embed Summary` | `/api/embed` | url `…/embeddings`, model `text-embedding-v3`, same auth header |

> **Footgun:** DashScope `/embeddings` returns `data[0].embedding`, not Ollama's
> `embeddings[0]`/`embedding`. The downstream `Query Qdrant` and `Upsert Summary To
> Qdrant` nodes read `embeddings?.[0] || embedding` — extend them to also try
> `… || $('Embed Query').item.json.data?.[0]?.embedding` (and the Embed Summary one).

**Pass bar:** grep the workflow shows no remaining `OLLAMA_`/`ollama` in the judged path.

---

## Phase 5 — End-to-end smoke

```bash
# orchestrator: manifest -> ingest -> retrieve (paths/payload per the workflow's webhook)
curl -s -X POST http://localhost:5678/webhook/local-echo-memory \
  -H 'Content-Type: application/json' \
  -d '{"action":"ingest","agent":"echo","session_id":"smoke-1","transcript_text":"Connor prefers tabs over spaces."}'

# git-committer reviewer
curl -s -X POST http://localhost:5678/webhook/git-committer-review \
  -H 'Content-Type: application/json' \
  -d "{\"diff\": $(git -C /home/cbk/qwen-agent-collective diff HEAD~1 | head -c 4000 | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')}"

# run the cron workflows once from the n8n UI (Execute Workflow), then check events:
docker exec -i brain_postgres psql -U collective -d collective \
  -c "SELECT event_type, count(*) FROM memory_events GROUP BY 1 ORDER BY 1;"
```

**Pass bar:**
- [ ] ingest returns candidate id(s); `memory_review_queue` / `memory_facts` gains rows; Qdrant `shared`/`echo_private` gains points.
- [ ] reviewer returns `{verdict, role_findings, metric:{delta…}}`.
- [ ] prune/digest/recap each write a `memory_events` row when executed.

---

## Phase 6 — Report back

State per phase: pass/fail + the pass-bar evidence (counts, HTTP codes, the verdict
JSON). List anything blocked (port clashes, model access, n8n version quirks) with the
exact error. Don't mark the brain "done" until Phase 5 is green — that's the brain.md
Definition of Done (DashScope-only path, 6 agents + collections, manifest/ingest/
retrieve verified). Alibaba Cloud deploy + proof file is the separate next milestone.
