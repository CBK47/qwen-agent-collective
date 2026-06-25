# qwen-agent-collective

One shared memory brain plus five specialist Qwen agents - one per hackathon track - built for the **Global AI Hackathon with Qwen Cloud**.

Every agent calls Qwen models on Alibaba Cloud Model Studio (DashScope) at runtime and reads/writes the shared brain. Build philosophy: breadth-first MVP - thin working skeletons across all five tracks first, polish later.

## Agents

| Directory | Track | Agent Name | Primary Model |
|---|---|---|---|
| [agents/memory-echo](agents/memory-echo/) | Track 1 - MemoryAgent | memory-echo | text-embedding-v3 + qwen-plus |
| [agents/showrunner](agents/showrunner/) | Track 2 - AI Showrunner | showrunner | qwen-plus |
| [agents/git-committer](agents/git-committer/) | Track 3 - Agent Society | git-committer | qwen2.5-coder-32b-instruct |
| [agents/open-translate](agents/open-translate/) | Track 4 - Autopilot | open-translate | qwen-plus |
| [agents/skippy-concierge](agents/skippy-concierge/) | Track 5 - EdgeAgent | skippy-concierge | qwen-vl-max + qwen2-audio-instruct |

## Monorepo Layout

```
/brain/
  db/               Postgres + Qdrant schemas and seed data
  orchestrator/     n8n workflows wiring agents to the brain
/agents/
  memory-echo/      Track 1 - MemoryAgent
  showrunner/       Track 2 - AI Showrunner
  git-committer/    Track 3 - Agent Society
  open-translate/   Track 4 - Autopilot
  skippy-concierge/ Track 5 - EdgeAgent (multimodal)
/shared/            Common DashScope client + brain namespace contract
/infra/             Alibaba Cloud deploy config
/docs/
  architecture/     System design notes
  submission-kit/   Hackathon submission assets
```

## Shared Brain

All agents share a single brain backed by:

- **Postgres** - structured memory (facts, events, agent state)
- **Qdrant** - vector store for semantic recall
- **n8n** - orchestration and inter-agent messaging

Namespaces are prefixed: `shared.*` is readable by all agents; each agent also has a private namespace (e.g. `echo.private`).

## Setup

```bash
cp .env.example .env
# Fill in DASHSCOPE_API_KEY and connection strings
```

See [docs/architecture](docs/architecture/) for system design and [HACKATHON.md](HACKATHON.md) for submission details.

## Licence

MIT - see [LICENSE](LICENSE).
