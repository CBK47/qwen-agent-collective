# shared

Common utilities and contracts used by all agents.

## Contents (to be implemented)

- **DashScope client** - thin wrapper around the DashScope HTTP API for chat, embeddings, vision, and audio calls. All agents import from here; keeps auth and retry logic in one place.
- **Namespace contract** - defines every Qdrant collection name and Postgres schema prefix. Agents must use these constants rather than hard-coded strings.

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
