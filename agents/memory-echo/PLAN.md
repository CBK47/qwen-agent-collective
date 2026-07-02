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
- [x] Bring up the brain stack (`brain/docker-compose.yml`) + DashScope key.
- [x] Implement the brain client call for ingest then retrieve.
- [x] Track-1 demo harness: ingest facts → expire stale → recall under a tight budget.

## Phase 2 — submission-grade (the real demoable track)
- [x] Track-1 demo via `shared/brain.py`: ingest facts → expire stale → recall under a tight token budget
- [x] Custom WebUI front-end for this agent — branded, interactive demo surface (the public face for the video)
- [ ] Deploy on Alibaba Cloud (requires `oss2`/aliyunsdkcore — NOT DONE)
- [ ] Record a 60–90s demo video (required for submission) — NOT RECORDED
