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
- [ ] Add `qwen-vl` / `qwen2-audio` inputs + manual-grounded answers.
