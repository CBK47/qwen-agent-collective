# showrunner — kickoff plan

**Track 2 — AI Showrunner** · agent_id `showrunner`

## Signature
`qwen-plus` scriptwriting that turns brain events into a short video script — it
dramatizes what the other agents have been doing.

## Models (DashScope)
- `qwen-plus` (`QWEN_CHAT_MODEL`) — script generation from events

## Brain namespaces / sources
| Source | Access | Contents |
|---|---|---|
| `showrunner.private` | read/write | drafts, episode state |
| `memory_events` (Postgres) | read | cross-agent event log to dramatize |
| `shared.*` | read | context for the narrative |

Qdrant: `showrunner_private`.

## MVP (breadth-first)
One real DashScope call + one brain read/write:
- [ ] Brain stack + DashScope key (with a few `memory_events` present).
- [x] Generate a script from the last N events.
- [x] Add the script → short-video render step.
