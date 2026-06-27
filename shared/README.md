# shared

Common utilities and contracts used by all agents.

## Contents

- **agent.py**: `shared.agent.BaseAgent` defines the default lifecycle: receive task, read memory/conventions, generate work, self-review, validate, iterate, write memory, return result.
- **dashscope.py**: Shared Qwen/DashScope interface for chat, embeddings, streaming, diagnostics, retries, timeouts, structured logs, and model selection.
- **namespace.py**: Defines every Qdrant collection name and Postgres schema prefix. Agents must use these constants rather than hard-coded strings.
- **glossary.py**: Provides access to canonical term translations stored in Postgres.
- **code_conventions.py**: Defines language-specific style rules and conventions for code generation.

## Commands

```sh
python -m shared.dashscope doctor       # live credential + chat/embed check
python -m shared.dashscope doctor --no-network
python shared/smoke_test.py
python shared/probe.py
```

All agents should use `shared.dashscope.DashScopeClient` or the compatibility
helpers `chat()` and `embed()`. Do not create new direct DashScope/OpenAI clients
inside agent implementations.

## Namespace Reference

| Namespace | Owner | Type | Notes |
|---|---|---|---|
| `shared.glossary` | open-translate | Postgres | Canonical term translations |
| `shared.code-conventions` | git-committer | Postgres | Language and style rules |
| `echo.private` | memory-echo | Qdrant | Personal memory vectors |
| `git-committer.private` | git-committer | Qdrant | Commit history embeddings |
| `open-translate.private` | open-translate | Qdrant | Translation memory |
| `skippy.private` | skippy-concierge | Qdrant | User device inventory |
| `devices` | skippy-concierge | Postgres | Shared device database |
| `skippy_device_manuals` | skippy-concierge | Qdrant | Manual chunk embeddings |
| `showrunner.private` | showrunner | Qdrant + Postgres | Show bible and episode history |
