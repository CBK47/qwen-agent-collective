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

To get started, you need to set up your DashScope API key:

1. **Obtain your API key**:
   - Visit the [DashScope Console](https://dashscope.console.aliyun.com/)
   - Sign in with your Alibaba Cloud account
   - Navigate to "API Key Management" and copy your existing key or create a new one

2. **Set up the environment variables**:
   ```bash
   cp brain/.env.example brain/.env
   # Open brain/.env and replace the placeholder with your actual API key
   # Example:
   # DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

See [docs/architecture](docs/architecture/) for system design and [HACKATHON.md](HACKATHON.md) for submission details.

## Brain Client API

The brain client allows agents to ingest and retrieve data from the shared memory. Below are examples of how to use the `ingest` and `retrieve` functions.

### Ingest Data

To store data in the brain, use the `ingest` function. It accepts the following parameters:

- `data`: The content to store (string or structured data)
- `namespace`: The namespace to store under (e.g., `shared.memory` or `agent.private`)
- `metadata` (optional): Additional metadata for the entry

Example:

```python
from shared.brain_client import ingest

# Ingest a fact into the shared namespace
ingest(
    data="The Eiffel Tower is in Paris",
    namespace="shared.facts",
    metadata={"source": "wikipedia", "category": "geography"}
)
```

### Retrieve Data

To fetch data from the brain, use the `retrieve` function. Parameters:

- `query`: The search query (for vector search) or key (for structured)
- `namespace`: The namespace to search in
- `top_k` (optional): Number of results to return (default 5)
- `filter` (optional): Additional filters for structured data

Example:

```python
from shared.brain_client import retrieve

# Retrieve top 3 facts related to geography
results = retrieve(
    query="geography",
    namespace="shared.facts",
    top_k=3
)

for result in results:
    print(result.data)
```

## Developer Commands

Create a local Python environment before running tests:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
```

```bash
make doctor   # live DashScope/Qwen credential diagnostics
make test     # offline unit tests
make smoke    # live chat + embedding smoke test
make probe    # live model capability probe
```

Architecture review and autonomous-worker decisions live in
[docs/architecture/repository-review.md](docs/architecture/repository-review.md)
and [docs/architecture/autonomous-development.md](docs/architecture/autonomous-development.md).

## Licence

MIT - see [LICENSE](LICENSE).
