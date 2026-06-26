# docs/architecture

System design notes for the qwen-agent-collective.

## Planned Contents

- [Repository review](repository-review.md) - current architecture, blockers, debt, and next implementation steps.
- [Autonomous development architecture](autonomous-development.md) - worker harness recommendation, memory taxonomy, and continuous-improvement loop.
- High-level architecture diagram (agents -> brain -> DashScope).
- Namespace contract rationale.
- Data flow: how an agent call goes from user input to Qwen API to brain write.
- Sequence diagrams for each agent's core loop.

## Key Design Decisions

- Single shared brain (Postgres + Qdrant) rather than per-agent databases - keeps cross-agent recall simple
- n8n is optional polish, not the critical path - demo agents call the brain client in-process first
- DashScope client lives in `/shared/` - one auth path, one retry policy, one model-selection policy
- Agent lifecycle lives in `shared.agent.BaseAgent` - receive task, read memory/conventions, generate, self-review, validate, iterate, write memory
- Breadth-first MVP: all five agents reach "thin working skeleton" before any one is polished
