# open-translate — kickoff plan

**Track 4 — Autopilot** · agent_id `open-translate`

## Signature
`qwen-plus` multilingual translation + a translation memory, with human-in-the-loop
(HITL) approval before glossary terms become shared.

## Models (DashScope)
- `qwen-plus` (`QWEN_CHAT_MODEL`) — translate + propose glossary terms

## Brain namespaces
| Namespace | Access | Contents |
|---|---|---|
| `open-translate.private` | read/write | translation memory |
| `shared.glossary` | read; write via review queue | approved term translations |
| `shared.*` | read | projects, people, architecture |

Qdrant: `open-translate_private`.

## MVP (breadth-first)
One real DashScope call + one brain read/write:
- [x] Brain stack + DashScope key.
- [x] Translate a sample string with glossary pulled from the brain.
- [ ] Wire translation-memory reuse + the HITL approval path to `shared.glossary`.
