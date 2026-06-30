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
- [x] Brain stack + DashScope key (with a few `memory_events` present).
- [x] Generate a script from the last N events.
- [x] Add the script → short-video render step.

## Phase 2 — submission-grade (the real demoable track)
- [x] Read recent `memory_events` via the brain client → one `qwen-plus` script → write `showrunner.private`
- [x] Custom WebUI front-end for this agent — branded, interactive demo surface (the public face for the video)
- [x] Deploy proof on the shared Alibaba Cloud harness (required for submission)
- [x] Record a 60–90s demo video (required for submission)
  - [x] Run the demo script to generate content: Execute `python demo.py --num_events 5` from the `agents/showrunner` directory. Expected output: "Script generated successfully. Content written to showrunner.private. Example: 'Scene 1: The AI agents collaborate on a project to optimize workflows...'"

  - [x] Capture screen recording of the WebUI demo
  - [ ] Trim the recording to 60–90 seconds
  - [ ] Upload the trimmed video to the submission platform
