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
- [x] Wire translation-memory reuse + the HITL approval path to `shared.glossary`.

## Phase 2 — submission-grade (the real demoable track)
- [x] `translate.py` CLI verified (`--help` OK); glossary + QA-gate path implemented (NOTE: broken duplicate `translator.py` exists — delete it)
- [x] Custom WebUI front-end for this agent — branded, interactive demo surface (the public face for the video)
- [ ] Deploy proof on the shared Alibaba Cloud harness (required for submission) — NOT DONE
- [ ] Record a 60–90s demo video (required for submission) — NOT RECORDED
