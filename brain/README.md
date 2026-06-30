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

## API Usage

The brain client API is frozen. All agents must import from `shared.brain.py` to prevent forks and ensure consistency across agents for submission.

## Setup

To initialize the brain stack:

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Set your DashScope API key in the `.env` file:
   ```env
   DASHSCOPE_API_KEY=your_api_key_here
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

## Agent Demos

- [Echo](demo/echo/README.md)
- [Skippy](demo/skippy/README.md)
- [Maya](demo/maya/README.md)
- [Jake](demo/jake/README.md)
- [Luna](demo/luna/README.md)
