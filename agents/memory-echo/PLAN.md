# memory-echo — kickoff plan

**Track 1 — MemoryAgent** · agent_id `echo`

## Signature
Embeddings + governed recall under a token budget. The reference agent for the
shared brain: demonstrates accumulate → forget → recall end to end.

## Models (DashScope)
- `text-embedding-v3` (`QWEN_EMBED_MODEL`) — embed memories/queries (dim 1024)
- `qwen-plus` (`QWEN_CHAT_MODEL`) — rank/summarise recalled memories

## Brain namespaces
| Namespace | Access | Contents |
|---|---|---|
| `echo.private` | read/write | personal memories + embeddings |
| `shared.*` | read | glossary, agent events, cross-agent facts |

Qdrant: `echo_private`, `echo_chat_chunks`, `echo_docs`.

## MVP (breadth-first)
One real DashScope call + one brain read/write:
- **Write:** embed a memory (`text-embedding-v3`) → Qdrant `echo_private`; fact row → Postgres.
- **Read:** `retrieve` approved facts honoring `expires_at`, ranked + truncated to a budget.

## First commands on Mac
- [ ] Bring up the brain stack (`brain/docker-compose.yml`) + DashScope key.
- [ ] Implement the brain client call for `ingest` then `retrieve`.
- [ ] Track-1 demo harness: ingest facts → expire stale → recall under a tight budget.
