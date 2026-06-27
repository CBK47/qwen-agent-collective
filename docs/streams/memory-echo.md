# Stream: Memory / Echo (the Track-1 agent)

- **Track:** 1 (MemoryAgent)
- **Tier:** core
- **Goal:** the agent face of the brain — demonstrates accumulate, forget, and recall
  under a limited context budget, with a striking visual.
- **Why Qwen:** `qwen-plus` summarise/extract on ingest; `text-embedding-v3` for
  semantic recall.
- **Brain namespace:** `echo.private` + reads `shared.*`.

## Current state
- Brain schema + governance in place (see `brain.md`).
- **Track-1 demo harness** being built in `brain/demo/` (Postgres-direct
  accumulate→forget→recall-under-budget).
- **Brain-at-work visualization** being built in `brain/viz/` (ingest/forget/recall
  animation, budget slider).

## MVP bar
A runnable demo that ingests facts, forgets stale ones, and recalls the best facts
under a tight token budget — plus the viz playing the same story.

## Next steps (execute in order)
1. Land the **demo harness** (`brain/demo/`): verify `run.sh` brings up Postgres,
   seeds, and `track1_demo.py` prints the 3 beats with passing asserts.
2. Land the **viz** (`brain/viz/`): confirm it plays `sample-events.json` and the
   budget slider re-runs recall selection live.
3. **Wire viz → real data (optional polish):** replace `sample-events.json` via the
   documented `loadEvents()` seam with output from the demo harness / brain `retrieve`.
4. Add **echo identity/prompts** (`prompts/echo/`) — system + retrieval + identity.
5. Add a `--semantic` path to the harness that routes recall through the orchestrator
   `retrieve` action (Qdrant + Qwen embeddings) once the DashScope port is live.
6. Record the **<3-min demo video**: ingest → forget → recall-under-budget, narrated
   over the viz. Architecture diagram + `HACKATHON.md`.

## Dependencies
- Brain stream (DashScope port) for the semantic recall path and live viz wiring.
- Demo harness + viz agents (in flight).

## Definition of done
- [ ] Demo harness runs green (3 beats, asserts pass)
- [ ] Viz plays the story; budget slider works
- [ ] Echo prompt pack present
- [ ] Semantic recall path verified against the deployed brain
- [ ] Diagram + `HACKATHON.md` + demo video
