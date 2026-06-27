# Brain workflows (n8n)

A handful of importable n8n workflows that plug into the existing brain
(Postgres + Qdrant + DashScope) alongside `../n8n-memory-orchestrator.json`.
Import each JSON via **n8n → Workflows → Import from File**.

| File | Track | Trigger | What it does |
|------|-------|---------|--------------|
| [memory-prune-nightly.json](memory-prune-nightly.json) | 1 (FORGET) | cron 03:00 | Expires facts past `expires_at`, logs one `memory_event`. Pure SQL, no LLM. |
| [review-queue-digest.json](review-queue-digest.json) | 1 (ACCUMULATE) | cron 08:00 | `qwen-plus` recommends approve/reject/hold per pending candidate → digest event. **Recommends only — never writes `memory_facts`** (human gate). |
| [git-committer-pr-review.json](git-committer-pr-review.json) | 3 | `POST /webhook/git-committer-review` | 3 role reviewers (`qwen3-coder`, parallel) → negotiation (`qwen-plus`) → one verdict + a single-agent baseline metric. |
| [showrunner-recap-nightly.json](showrunner-recap-nightly.json) | 2 | cron 23:00 | Reads 24h of `memory_events` under a token budget → `qwen-plus` recap "episode" → saved to `showrunner.private`. |

## Setup (each workflow tells you in a sticky note)
1. **Postgres credential** — every Postgres node ships with `id: REPLACE_ME`; open
   the node and pick your brain Postgres credential.
2. **DashScope env** in n8n (`DASHSCOPE_API_KEY`, `DASHSCOPE_BASE_URL`,
   `QWEN_CHAT_MODEL`, `QWEN_CODER_MODEL`) — same names as `/.env.example`.
3. Activate. Cron workflows run on schedule; the PR-review one waits on its webhook.

## Notes
- LLM/free text headed for SQL is single-quote-escaped in the Code node (`''`), so
  `executeQuery` interpolation can't be broken by quotes. ponytail: escape-in-code is
  the lazy-safe path; switch to parameterised inserts if a field ever carries `$`-exprs.
- Code nodes call DashScope via `this.helpers.httpRequest` (self-hosted n8n).
- Test the PR-review logic offline: `node` against the jsCode with a mocked
  `httpRequest` (see commit message / scratchpad) — verifies fan-out + metric.

To POST a diff to the reviewer:
```bash
curl -X POST http://localhost:5678/webhook/git-committer-review \
  -H 'Content-Type: application/json' \
  -d "{\"diff\": $(git diff HEAD~1 | jq -Rs .)}"
```
