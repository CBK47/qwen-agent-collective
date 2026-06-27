# Stream: Skippy multimodal concierge

- **Track:** 5 (EdgeAgent)
- **Tier:** stretch (highest complexity)
- **Goal:** one edge device that orchestrates the whole Qwen model family + the brain —
  sees, hears, reasons, remembers, and acts locally in the home.
- **Why Qwen:** vision `qwen-vl-max` + speech `qwen2-audio-instruct` + chat `qwen-plus`
  (+ CosyVoice TTS later) — sophisticated multi-API orchestration (Innovation points).
- **Brain namespace:** `skippy.private` + `devices` + `skippy_device_manuals`.

## Current state
- Code being **seeded from `AI-Multimodal-Orchestration`** (local-session port) into
  `agents/skippy-concierge/src/` — see that repo's `PROVENANCE.md` / `NOTES.md`.
- Skippy identity already in the brain schema (`devices`, skippy namespaces/collections).

## MVP bar
A loop that captures one vision + one audio input, sends derived features to Qwen on
DashScope, reasons with brain context, and triggers one local action — with a clear
privacy boundary and an offline fallback path.

## Next steps (execute in order)
1. **Land the port** — confirm `src/perception`, `src/models`, `src/orchestrator`,
   `src/actuation`, `src/brain` exist with the reusable code; clear the `NOTES.md` TODOs.
2. **Model clients → DashScope** — point `src/models` at `qwen-vl-max`,
   `qwen2-audio-instruct`, `qwen-plus` via env (`DASHSCOPE_*`); replace any stubs.
3. **Perceive → reason → act loop** — wire `src/orchestrator`: capture vision/audio →
   derive features → Qwen reason (with brain context) → choose a local action.
4. **Brain reads** — load device registry + preferences from `skippy.private` +
   `devices`; write events back via `ingest`.
5. **Local actuation** — one real action via Home Assistant / MQTT.
6. **Privacy boundary** — raw frames/audio stay on-device; only derived features leave.
7. **Offline fallback** — cached policy / local response when the network drops.
8. Deploy the cloud side on Alibaba Cloud + proof; diagram; `HACKATHON.md`; demo:
   perceive → cloud reason → local act → offline fallback.

## Dependencies
- The local-session port (in flight) must land first.
- Brain (devices + skippy.private). DashScope multimodal model access.

## Definition of done
- [ ] perceive → reason → act loop runs with Qwen on DashScope
- [ ] Reads/writes brain (`skippy.private`, `devices`)
- [ ] One real local action + privacy boundary + offline fallback
- [ ] Deployed cloud side on Alibaba Cloud + proof
- [ ] Diagram + `HACKATHON.md` + demo video
