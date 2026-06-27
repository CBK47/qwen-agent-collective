# Local Echo / Skippy MVP Implementation Plan

## Goal

Build a local-first AI stack with:
- Open WebUI as the main chat and control surface
- Ollama as the local model runtime
- n8n as the workflow, memory-ingestion, and tool-orchestration layer
- PostgreSQL as the structured memory and state database
- Qdrant as the semantic retrieval / RAG store
- Langfuse for prompt management and observability
- Obsidian as the human-editable knowledge vault

Shared infrastructure, separate agent identities:
- **Echo** = serious collaborator, memory-heavy, project and life-admin oriented
- **Skippy** = fun home-ops / IoT / status-chat agent with tighter tool permissions

## Why use the n8n AI Starter Kit as the base

Use the official Self-hosted AI Starter Kit as the reference baseline because it already combines:
- n8n
- Ollama
- Qdrant
- PostgreSQL

Then extend that baseline with:
- Open WebUI
- Langfuse
- an Obsidian vault mount
- your custom memory schema and workflows

## Architecture principles

1. One source of truth per concern
   - Open WebUI is the UI
   - n8n is the orchestration layer
   - Postgres is the structured memory/state store
   - Qdrant is the semantic retrieval store
   - Obsidian is the human-editable knowledge vault
   - Langfuse is the observability/prompt-management layer

2. Do not let memory live in random places
   - Keep Open WebUI's own long-term memory features disabled or minimally used
   - Keep canonical memory in Postgres + Qdrant
   - Treat Obsidian as curated source material, not as the only memory backend

3. Separate agents by namespace
   - different system prompts
   - different Postgres namespaces
   - different Qdrant collections
   - different permissions and tools
   - different export bundles

4. Keep the first MVP modest but real
   - one main memory API workflow
   - one ingestion pattern for chats and documents
   - one retrieval pattern
   - one manifest/export pattern
   - optional future workflows for approvals, promotion, pruning, and device actions

## Service topology

### Services
- `open-webui`
- `ollama`
- `n8n`
- `postgres`
- `qdrant`
- `langfuse-web`
- `langfuse-worker`
- `clickhouse`
- `redis` or `valkey`
- optional object store later for fuller Langfuse deployment patterns

### Shared internal Docker network
- `ai_core_net`

### Persistent volumes
- `postgres_data`
- `qdrant_storage`
- `ollama_data`
- `n8n_data`
- `openwebui_data`
- `langfuse_postgres_data`
- `langfuse_clickhouse_data`
- `langfuse_redis_data`
- `obsidian_vault`
- `stack_backups`

## Responsibility split

### Open WebUI
Use as the main user-facing chat UI.
Responsibilities:
- primary chat experience
- model presets
- chat organisation
- optional tools / MCP / OpenAPI tool servers
- optional future Pipelines for advanced proxy logic

Avoid storing canonical long-term memory here.

### Ollama
Use as the inference layer.
Suggested model roles:
- `echo_chat_model`
- `echo_reasoning_model`
- `skippy_chat_model`
- `embedding_model`

Do not rely on Ollama for stateful memory.

### n8n
Use as the memory and automation spine.
Responsibilities:
- ingest chats
- ingest docs / notes
- call Ollama for extraction and embeddings
- write structured memory to Postgres
- write semantic chunks to Qdrant
- expose webhook endpoints or future MCP/OpenAPI tools
- run promotion / cleanup / review workflows
- run home-ops workflows for Skippy

### PostgreSQL
Use for structured, queryable memory and operational state:
- user profile
- preferences
- people
- projects
- tasks
- devices
- session log metadata
- session summaries
- memory review queue
- approved memory facts
- tool permission policies
- source registry
- retrieval feedback

### Qdrant
Use for semantic retrieval over:
- chat chunks
- note chunks
- project docs
- manuals
- wiki pages
- SOPs
- home automation reference docs

### Langfuse
Use for:
- prompt versioning
- evals
- observability
- trace analysis where supported
- model and prompt comparison

### Obsidian
Use as the human-editable knowledge layer:
- curated notes
- project pages
- people pages
- playbooks
- daily notes
- architecture decisions
- home automation docs

## Recommended folder layout

```text
local-echo/
├── docker/
│   ├── compose/
│   │   ├── docker-compose.yml
│   │   ├── docker-compose.override.yml
│   │   └── .env
│   ├── backups/
│   └── init/
├── data/
│   ├── postgres/
│   ├── qdrant/
│   ├── ollama/
│   ├── n8n/
│   ├── openwebui/
│   ├── langfuse/
│   └── exports/
├── prompts/
│   ├── echo/
│   └── skippy/
├── memory/
│   ├── manifests/
│   ├── blobs/
│   └── snapshots/
├── obsidian/
│   └── local-echo-vault/
│       ├── 00-inbox/
│       ├── 10-people/
│       ├── 20-projects/
│       ├── 30-systems/
│       ├── 40-home-ops/
│       ├── 50-daily/
│       └── 90-exports/
└── workflows/
    └── n8n/
```

## PostgreSQL schema for MVP

### Core tables
- `agents`
- `users`
- `sessions`
- `messages`
- `memory_facts`
- `memory_events`
- `memory_review_queue`
- `projects`
- `people`
- `devices`
- `source_registry`
- `retrieval_feedback`

### Example meanings

#### `agents`
- `agent_id`
- `agent_slug`
- `display_name`
- `system_prompt_path`
- `retrieval_prompt_path`
- `is_active`

#### `sessions`
- `session_id`
- `agent_id`
- `user_id`
- `channel`
- `source_app`
- `started_at`
- `ended_at`
- `title`
- `summary_short`
- `summary_long`
- `tags_json`

#### `memory_facts`
- `fact_id`
- `agent_id`
- `user_id`
- `memory_namespace`
- `fact_type`
- `subject`
- `predicate`
- `object_text`
- `confidence`
- `source_session_id`
- `source_note_path`
- `status`
- `expires_at`
- `created_at`
- `updated_at`

#### `memory_events`
- `event_id`
- `agent_id`
- `user_id`
- `event_type`
- `title`
- `event_text`
- `event_time`
- `source_session_id`
- `metadata_json`

#### `memory_review_queue`
- `candidate_id`
- `agent_id`
- `session_id`
- `candidate_type`
- `payload_json`
- `confidence`
- `status`
- `created_at`
- `reviewed_at`

## Qdrant collection design

### Echo collections
- `echo_chat_chunks`
- `echo_docs`
- `echo_obsidian`
- `echo_project_refs`

### Skippy collections
- `skippy_chat_chunks`
- `skippy_home_docs`
- `skippy_device_manuals`
- `skippy_obsidian`

### Shared collections
- `shared_reference`
- `shared_policies`

### Suggested payload fields for every Qdrant point
- `agent`
- `source_type`
- `source_id`
- `source_path`
- `session_id`
- `doc_title`
- `chunk_index`
- `tags`
- `created_at`
- `updated_at`
- `sensitivity`
- `namespace`

## Obsidian integration design

Obsidian stores notes as local markdown files in a vault. Use that to your advantage.

### Recommended role
Use it as:
- editable notebook
- project wiki
- daily notes
- architecture journal
- home-ops docs
- manual curation zone before promotion into durable memory

### Recommended vault structure
- `00-inbox/`
- `10-people/`
- `20-projects/`
- `30-systems/`
- `40-home-ops/`
- `50-daily/`
- `90-exports/`

### Recommended note frontmatter
```yaml
agent_scope: echo
memory_class: source
tags:
  - project
  - planning
status: active
project: local-echo
confidence: human-curated
```

### How Obsidian fits the stack
1. You write or edit notes in Obsidian.
2. n8n scans the vault on a schedule.
3. Changed notes are chunked and embedded.
4. Chunks go to Qdrant.
5. Important metadata goes to Postgres `source_registry`.
6. Specific reviewed facts can be promoted into `memory_facts`.

## Langfuse design notes

### Use it for
- prompt versioning
- comparing prompt revisions
- later evals
- custom services or pipelines that emit traces
- tracking ingestion pipeline quality over time

### MVP reality
- prompt management is easy to add in n8n
- native n8n tracing is not currently available

### Practical MVP pattern
- keep prompt files in Git and optionally mirror them into Langfuse Prompt Management
- add Langfuse later to custom microservices or Open WebUI pipelines where tracing is easier
- log critical workflow outputs into Postgres for operational debugging from day one

## Main workflow: `local-echo-memory-orchestrator`

Purpose:
- provide a single API-like workflow with three actions:
  - `retrieve`
  - `ingest`
  - `manifest`

### Action: `retrieve`
Input:
- `agent`
- `session_id`
- `query`
- optional tags / namespace

Flow:
1. normalise payload
2. fetch approved structured facts from Postgres
3. embed the query using Ollama
4. query Qdrant
5. return a combined context bundle

### Action: `ingest`
Input:
- `agent`
- `session_id`
- `messages`
- optional `source_type`
- optional `source_path`

Flow:
1. normalise transcript
2. summarise and extract memory candidates with Ollama
3. store session summary in Postgres
4. store candidate memories in `memory_review_queue`
5. embed the summary or chunks with Ollama
6. upsert them to Qdrant
7. return an ingestion receipt

### Action: `manifest`
Input:
- `agent`

Flow:
1. generate the canonical memory names for that agent
2. return collection names, namespaces, export names, prompt names

## Additional workflows to add after MVP
- `obsidian-vault-sync`
- `memory-promotion-review`
- `skippy-homeops-dispatcher`
- `backup-and-export`

## Memory blobs / export bundle design

### Global / shared
- `manifest.global.yaml`
- `user.connor.profile.json`
- `preferences.global.json`
- `people.registry.json`
- `projects.registry.json`
- `shared.policies.json`
- `shared.reference.index.json`

### Echo
- `agent.echo.identity.md`
- `agent.echo.system-prompt.md`
- `agent.echo.retrieval-prompt.md`
- `agent.echo.memory-manifest.yaml`
- `echo.memory-facts.jsonl`
- `echo.memory-events.jsonl`
- `echo.session-summaries.jsonl`
- `echo.review-queue.jsonl`
- `echo.qdrant-collections.json`
- `echo.obsidian-export.md`

### Skippy
- `agent.skippy.identity.md`
- `agent.skippy.system-prompt.md`
- `agent.skippy.retrieval-prompt.md`
- `agent.skippy.memory-manifest.yaml`
- `skippy.memory-facts.jsonl`
- `skippy.memory-events.jsonl`
- `skippy.session-summaries.jsonl`
- `skippy.review-queue.jsonl`
- `skippy.qdrant-collections.json`
- `skippy.device-registry.json`
- `skippy.obsidian-export.md`

### Per-session exports
- `session.<agent>.<session_id>.summary.json`
- `session.<agent>.<session_id>.messages.jsonl`
- `session.<agent>.<session_id>.retrieval.json`
- `session.<agent>.<session_id>.ingest-receipt.json`

## Recommended implementation order

### Phase 1: platform bring-up
1. Start from the n8n AI Starter Kit reference.
2. Bring up Postgres, Qdrant, Ollama, n8n.
3. Add Open WebUI.
4. Add Langfuse.
5. Confirm Docker networking.

Exit criteria:
- Open WebUI can call Ollama
- n8n can call Ollama
- n8n can talk to Postgres
- n8n can talk to Qdrant
- Langfuse is reachable

### Phase 2: data model
1. Create Postgres schema.
2. Create Qdrant collections.
3. Create prompt files.
4. Create initial Obsidian vault structure.

### Phase 3: workflow import and credential mapping
1. Import the included n8n workflow template.
2. Create credentials for Postgres, Ollama, and Qdrant.
3. Set environment variables and URLs.
4. Test the `manifest` action first.

### Phase 4: ingestion test
1. Send a small Echo transcript to the `ingest` action.
2. Verify rows appear in Postgres.
3. Verify chunks appear in Qdrant.
4. Confirm receipt payload is correct.

### Phase 5: retrieval test
1. Send a `retrieve` query.
2. Confirm structured facts come back.
3. Confirm Qdrant hits come back.
4. Confirm the context bundle is usable in Open WebUI or a future MCP/OpenAPI tool.

### Phase 6: Obsidian sync
1. Create the vault sync workflow.
2. Ingest notes.
3. Tag and retrieve them semantically.

### Phase 7: hardening
1. backups
2. auth
3. rate limits
4. network restrictions
5. tool permissions
6. review queues
7. retention rules

## Security / sanity rules
- Do not give Skippy write-capable tools on day one.
- Keep dangerous actions behind approval gates.
- Do not let Open WebUI Workspace Tools be open to untrusted users.
- Keep canonical memory in Postgres/Qdrant.
- Use UTC everywhere for timestamps.
- Back up Postgres and Qdrant separately.
- Keep prompts and manifests in Git.
- Version your export bundles.

## Suggested next artefacts after this plan
1. `docker-compose.yml`
2. `.env.example`
3. `postgres-init.sql`
4. `obsidian-vault-sync` workflow
5. `memory-promotion-review` workflow
6. prompt pack for Echo and Skippy
