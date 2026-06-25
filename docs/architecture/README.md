# docs/architecture

System design notes for the qwen-agent-collective.

## Planned Contents

- High-level architecture diagram (agents -> brain -> DashScope)
- Namespace contract rationale
- Data flow: how an agent call goes from user input to Qwen API to brain write
- Sequence diagrams for each agent's core loop

## Key Design Decisions

- Single shared brain (Postgres + Qdrant) rather than per-agent databases - keeps cross-agent recall simple
- n8n as the orchestration layer - low-code, easy to inspect, swappable
- DashScope client lives in `/shared/` - one auth path, one retry policy
- Breadth-first MVP: all five agents reach "thin working skeleton" before any one is polished
