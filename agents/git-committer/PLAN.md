# git-committer — kickoff plan

**Track 3 — Agent Society** · agent_id `git-committer`

## Signature
`qwen2.5-coder` multi-role PR review with a negotiated verdict — several reviewer
personas argue, then converge on one decision.

## Models (DashScope)
- `qwen2.5-coder-32b-instruct` (`QWEN_CODER_MODEL`) — per-role code review
- `qwen-plus` (`QWEN_CHAT_MODEL`) — negotiate/synthesize the final verdict

## Brain namespaces
| Namespace | Access | Contents |
|---|---|---|
| `git-committer.private` | read/write | review history, persona state |
| `shared.code-conventions` | read; write via review queue | house style / conventions |
| `shared.*` | read | architecture, glossary, etc. |

Qdrant: `git-committer_private`.

## MVP (breadth-first)
One real DashScope call + one brain read/write:
- **Read:** pull `shared.code-conventions` from the brain.
- **Call:** one `qwen2.5-coder` review pass over a sample diff applying those conventions.
- **Write:** verdict → `git-committer.private`; any new convention → `memory_review_queue`.

## First commands on Mac
- [x] Brain stack + DashScope key.
- [x] Single-role review over a fixed diff, conventions pulled from the brain.
- [x] Add the multi-role negotiation loop + verdict synthesis.

## Phase 2 — submission-grade (the real demoable track)
- [ ] Read `shared.code-conventions` via the brain client → one `qwen2.5-coder` review pass over a fixed diff
- [ ] Custom WebUI front-end for this agent — branded, interactive demo surface (the public face for the video)
- [ ] Deploy proof on the shared Alibaba Cloud harness (required for submission)
- [ ] Record a 60–90s demo video (required for submission)

- [ ] Fix `debate_prototype.py`: it imports the nonexistent `brain.conventions`; either inline the personas or point it at the working `review.py` pipeline.
