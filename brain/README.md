# brain

Shared memory layer used by all five agents.

## Components

| Directory | Role |
|---|---|
| [db/](db/) | Postgres (structured facts, agent state) + Qdrant (vector embeddings) |
| [orchestrator/](orchestrator/) | n8n workflows for inter-agent messaging and brain sync |

## Namespaces

All collections/tables are namespaced. `shared.*` is readable by every agent. Each agent also has a private namespace (e.g. `echo.private`, `skippy.private`).

See [../shared/](../shared/) for the namespace contract.
