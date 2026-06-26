# Autonomous Development Architecture

Date: 2026-06-26

## Objective

Turn the collective into an autonomous software company loop:

```text
choose task -> branch -> implement -> test -> self-review -> update docs
-> write memory -> open PR -> human final review
```

The first implementation target is not a fully unsupervised company. It is a
safe, repeatable worker loop that reduces human effort to priority, architecture,
and final approval.

## Harness Options

| Option | Fit | Notes |
|---|---|---|
| Codex CLI / Codex | Best immediate fit | Already optimized for repository-local coding, terminal validation, patches, and PR-shaped work. Keep as the default supervised worker harness. |
| Claude Code | Strong human-in-the-loop fit | Excellent coding UX and hooks; already used by `memory-echo/session_logger.py`. Keep as a compatible operator surface, but do not make the platform depend on Anthropic-only behavior. |
| OpenCode | Good local/open option | Open source terminal, desktop, and IDE agent with project rules, provider configuration, and custom commands. Good candidate for running Qwen-backed local workers once provider config is proven. |
| OpenHands | Strong longer-term orchestration fit | Provides agent canvas, CLI, SDK, cloud/enterprise paths, integrations, and local/server execution. Heavier than this repo needs today, but attractive once we need queued multi-worker execution. |
| OpenAI Codex cloud/PR workflows | Strong future fit | Good target for issue-to-PR automation if GitHub integration becomes the primary task queue. |
| Local Qwen coding models | Required inference strategy | Use Qwen/DashScope models through `shared.dashscope`. Do not let each harness call its own model endpoint independently. |

References checked on 2026-06-26:

- OpenHands docs: https://docs.openhands.dev/overview/introduction
- OpenCode docs: https://opencode.ai/docs/
- OpenAI Codex repository: https://github.com/openai/codex
- Claude Code docs: https://code.claude.com/docs/en/overview
- Alibaba Model Studio docs: https://help.aliyun.com/en/model-studio/what-is-model-studio

## Recommendation

Use a layered strategy:

1. **Now:** Codex/Claude Code as supervised autonomous workers, with the repo
   providing the shared Qwen client, task conventions, tests, and docs checks.
2. **Next:** Add a repo-native `shared/brain.py` memory client and simple task
   table/issue sync. Workers can choose tasks from that queue.
3. **Later:** Evaluate OpenHands SDK/Agent Canvas for multi-worker scheduling if
   the project needs concurrent agents, hosted workspaces, Slack/Jira/Linear, or
   richer permission controls.
4. **Parallel option:** Test OpenCode with Qwen-compatible provider settings as a
   lightweight local worker once the core repo loop is stable.

Do not introduce OpenHands or another large framework before the memory keystone
exists. The current bottleneck is local brain runtime, not orchestration UI.

## Worker Contract

Every autonomous worker must:

1. Read `docs/architecture/repository-review.md`, `docs/architecture/README.md`,
   and relevant `agents/*/PLAN.md`.
2. Validate Qwen configuration with `python -m shared.dashscope doctor --no-network`.
3. Create or switch to a scoped branch.
4. Read memory through the future `shared.brain.retrieve()`.
5. Implement the smallest task slice.
6. Run `make test` and any task-specific validation.
7. Self-review for architecture drift, duplicated infrastructure, missing tests,
   and documentation impact.
8. Update docs/changelog/conventions when behavior changes.
9. Write lessons learned through `shared.brain.ingest()`.
10. Open a PR with validation output and residual risks.

## Continuous Improvement Hooks

Each completed task should trigger these checks:

| Check | First implementation | Later automation |
|---|---|---|
| Documentation review | PR checklist and `docs/architecture` update | Post-task agent reads diff and proposes README/architecture edits |
| README updates | Human/worker checklist | Diff classifier flags user-facing changes |
| Architecture updates | Required for shared/infrastructure changes | Agent writes ADR draft |
| Changelog updates | Add `CHANGELOG.md` before first release | Generate entry from merged PR metadata |
| Coding convention checks | `make test` plus self-review | `shared.code-conventions` memory retrieval and review agent |
| Issue generation | Manual notes in PR | Agent opens follow-up issues from TODOs, skipped tests, and review notes |

## Memory Taxonomy

Avoid a single undifferentiated vector store. Use separate stores and retention
rules:

| Memory type | Store | Access | Retention |
|---|---|---|---|
| Architecture memory | Postgres approved facts + `shared_reference` vectors | all agents read, review-queue writes | long-lived |
| Coding conventions | Postgres `shared.code-conventions` + vectors | all agents read, git-committer proposes writes | long-lived |
| Lessons learned | Postgres facts/events + agent-private vectors | owning agent writes, shared promotion by review | medium-lived |
| Agent logs | Postgres sessions/messages/events | owning agent writes, showrunner reads events | append-only with pruning policy |
| Project history | Git log + release/changelog docs | all agents read | permanent |
| Temporary working memory | task metadata or local scratch | owning worker only | expire after task completion |

## Immediate Build Order

1. Finish `shared/brain.py` over Postgres + Qdrant.
2. Add `brain/docker-compose.yml` for local Postgres/Qdrant.
3. Convert `memory-echo` from Markdown-only memory to brain ingest/retrieve.
4. Add plug-in discovery for `agents/*/agent.py`.
5. Add CI for `make test` and offline DashScope diagnostics.
6. Add a PR checklist that enforces docs, architecture, conventions, and future
   issue capture.

## Open Decisions

- Whether tasks live first in GitHub Issues, Postgres, or a simple YAML queue.
- Whether shared memory promotions are human-approved only or can be auto-approved
  for low-risk convention/doc facts.
- Whether the first deployed harness should be Alibaba ECS, Function Compute, or
  a simpler single VM for demo proof.
