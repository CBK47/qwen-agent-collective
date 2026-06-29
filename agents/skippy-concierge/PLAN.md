# skippy-concierge — kickoff plan

**Track 5 — EdgeAgent** · agent_id `skippy`

## Signature
`qwen-vl` + `qwen2-audio` + `qwen-plus` orchestrated multimodal home concierge that
acts locally on devices.

## Models (DashScope)
- `qwen-vl-max` (`QWEN_VL_MODEL`) — image/scene understanding
- `qwen2-audio-instruct` (`QWEN_AUDIO_MODEL`) — voice/audio understanding
- `qwen-plus` (`QWEN_CHAT_MODEL`) — orchestrate intent → device action

## Brain namespaces / scopes
| Scope | Access | Contents |
|---|---|---|
| `skippy.private` | read/write | concierge state, preferences |
| `devices` (Postgres) | read/write | device registry (`agent_scope='skippy'`) |
| `skippy_device_manuals` (Qdrant) | read | manual chunks for grounded answers |
| `shared.*` | read | cross-agent facts |

## MVP (breadth-first)
One real DashScope call + one brain read/write:
- [x] Brain stack + DashScope key; seed a couple of `devices` rows.
- [x] Single text→action path over the device registry.
- [x] Add `qwen-vl` / `qwen2-audio` inputs
- [x] manual-grounded answers

## Phase 2 — submission-grade (the real demoable track)
- [x] Seed `devices` rows → one text→action `qwen-plus` call over the registry via the brain client
- [x] Custom WebUI front-end for this agent — branded, interactive demo surface (the public face for the video)
- [x] Deploy proof on the shared Alibaba Cloud harness (required for submission)
- [x] Run skippy_demo.py to launch the demo interface
- [ ] Capture screen recording of the demo interaction (including voice commands if applicable)
- [ ] Trim the recording to 60-90 seconds, focusing on key demo points
- [ ] Upload the trimmed video to the submission platform
