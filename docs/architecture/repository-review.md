# Repository Review: Autonomous Qwen Collective

Date: 2026-06-26

## Current Architecture

The repository is a small monorepo for five hackathon agents that share one memory
brain and one Qwen/DashScope inference spine.

```text
agents/*              Track-specific agent plans and early prototypes
brain/db              Postgres schema for structured memory and governance
brain/orchestrator    n8n port plan, deferred from the critical path
brain/explorer        Demo UI and Qwen-backed grounded recall endpoint
shared                Shared Qwen client, namespace contract, agent loop primitives
infra                 Deployment placeholder
docs                  Architecture and submission material
```

The intended runtime path is:

```text
agent -> shared.agent.BaseAgent -> shared.dashscope.DashScopeClient
      -> DashScope OpenAI-compatible API
      -> memory read/write adapter (future shared.brain)
```

The memory storage design already exists in `brain/db/postgres-init.sql` and
`brain/memory-manifest.yaml`: Postgres stores sessions, messages, facts, events,
review queues, projects, people, and devices; Qdrant collections hold semantic
memory vectors.

## Existing Agent Implementations

The five agents are mostly scaffolded as README/PLAN files:

| Agent | State | Current implementation |
|---|---|---|
| `memory-echo` | partial | `session_logger.py` summarizes Claude Code sessions into `session-log.md`; no live brain client yet |
| `showrunner` | planned | prompt/model/namespace plan only |
| `git-committer` | planned | prompt/model/namespace plan only |
| `open-translate` | planned | prompt/model/namespace plan only |
| `skippy-concierge` | planned | multimodal plan only |

The only working agent-like code is `memory-echo/session_logger.py`. It uses
Qwen for session summaries, but it writes to a Markdown log rather than the
designed Postgres/Qdrant memory layer.

## Prompts And Configuration

Prompts currently live inline in scripts:

- `agents/memory-echo/session_logger.py`
- `docs/submission-kit/blogger.py`
- `brain/explorer/server.mjs`

Configuration is environment-variable based, with examples in `.env.example` and
`brain/.env.example`. The active `.env` is gitignored. The important model
selectors are:

- `QWEN_CHAT_MODEL`
- `QWEN_CODER_MODEL`
- `QWEN_VL_MODEL`
- `QWEN_AUDIO_MODEL`
- `QWEN_EMBED_MODEL`

The shared client now also supports:

- `QWEN_TIMEOUT_SECONDS`
- `QWEN_MAX_RETRIES`
- `QWEN_BACKOFF_BASE_SECONDS`
- `QWEN_TEMPERATURE`
- `QWEN_MAX_TOKENS`

## API And Secret Handling

DashScope is OpenAI-compatible, so the shared Python client uses the OpenAI SDK
against `DASHSCOPE_BASE_URL`. Alibaba Cloud documents Model Studio as
OpenAI-compatible and region-specific, with Singapore pay-as-you-go URLs shaped
like `https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1`.

References:

- Alibaba Model Studio overview: https://help.aliyun.com/en/model-studio/what-is-model-studio
- Alibaba Cline/OpenAI-compatible setup: https://help.aliyun.com/en/model-studio/cline
- Alibaba embedding model specs: https://help.aliyun.com/en/model-studio/embedding

Secrets are not committed: `.env` is ignored and `.env.example` contains only
placeholders. The active local key was validated by `python -m shared.dashscope doctor`.

## Shared Libraries

Implemented shared code now includes:

- `shared/dashscope.py`: single Python Qwen client with env loading, configurable
  models, retries, exponential backoff, timeouts, structured logs, streaming,
  diagnostics, and compatibility helpers.
- `shared/dashscope.mjs`: small Node wrapper used by Brain Explorer so the UI
  server no longer hand-rolls DashScope HTTP calls.
- `shared/agent.py`: reusable agent lifecycle template.
- `shared/namespaces.py`: namespace constants.
- `shared/probe.py` and `shared/smoke_test.py`: live diagnostics.

## Duplication

Current duplication is low but visible:

- Prompt construction is inline in each script rather than centralized per agent.
- The root `.env.example` and `brain/.env.example` differ in database defaults.
- Memory namespace concepts appear in README files, YAML manifest, SQL seeds, and
  Python constants. They need a generated consistency check.
- Brain Explorer keeps demo fixture data in `index.html` instead of reading the
  live brain.

## Missing Abstractions

The high-value missing pieces are:

1. `shared/brain.py`: direct Postgres + Qdrant memory adapter with `ingest`,
   `retrieve`, `manifest`, and review-queue helpers.
2. Prompt registry: move durable prompts out of scripts into versioned
   per-agent prompt files.
3. Agent plug-in loader: discover `agents/*/agent.py` modules that expose a
   common `build_agent()` entry point.
4. Validation runner: a reusable way for coding agents to run tests, lint, and
   repo-specific checks.
5. Continuous-improvement hooks: post-task documentation, architecture,
   changelog, convention, and issue-generation review.

## Technical Debt

- No real brain runtime yet. SQL/YAML exist, but no app code uses Postgres or
  Qdrant directly.
- No `brain/docker-compose.yml`, so the keystone local stack is still manual.
- n8n is documented but cut from the critical path; docs should be updated to
  label it optional polish, not primary architecture.
- The frontend explorer is useful for demos but contains a large static fixture
  file and no automated browser test.
- Tests were effectively absent before this pass.
- No CI workflow exists.
- Deployment is a placeholder.

## Immediate Blockers

1. Build `shared/brain.py` and `brain/docker-compose.yml`; without them four of
   five agents remain blocked on memory.
2. Connect `memory-echo` to the real brain, because it is the reference path for
   accumulate, forget, and recall.
3. Add minimal CI: unit tests plus `python -m shared.dashscope doctor --no-network`.
4. Create one deploy harness reused by all tracks, rather than five bespoke
   deployments.

## Opportunities For Autonomous Development

- Use `shared.agent.BaseAgent` as the plug-in contract for all five agents.
- Use `shared.dashscope.DashScopeClient` as the only Python inference interface.
- Add a task queue table or issue sync so AI workers can choose scoped tasks.
- Require every autonomous worker loop to:
  1. create a branch,
  2. read architecture/convention memory,
  3. implement narrowly,
  4. run tests,
  5. self-review,
  6. update docs,
  7. write memory,
  8. open a PR for human final review.
- Keep human effort focused on priority, architecture, and final merge approval.

## Decisions Made In This Pass

- Keep DashScope access in `shared/dashscope.py` and extend it rather than adding
  another client library.
- Preserve backward-compatible `chat()`, `embed()`, `client`, and model constants
  so current scripts continue to run.
- Add a small `shared/agent.py` framework but avoid a heavy orchestration
  dependency until the brain client exists.
- Route Brain Explorer's Qwen call through `shared/dashscope.mjs` to keep the
  "shared spine only" rule consistent across Python and Node surfaces.
