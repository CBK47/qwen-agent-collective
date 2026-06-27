# Stream: The Showrunner

- **Track:** 2 (AI Showrunner)
- **Tier:** stretch
- **Goal:** an agent that reads the shared brain and autonomously dramatizes the agent
  society's life into short recap episodes — and, early on, narrates the build itself
  (feeding the blog-post bonus prize).
- **Why Qwen:** `qwen-plus` scriptwriting/storyboarding from *distilled* brain memory —
  directly answers Track 2's "maximize quality under a limited token budget" by feeding
  `summary_short` + structured facts instead of raw logs. Brain = context compressor.
- **Brain namespace:** reads `shared.*` + `memory_events`; writes `showrunner.private`.

## Current state
- Not started. Lives at `agents/showrunner/` in `qwen-agent-collective`.
- Brain `memory_events` / session summaries are the source material.

## MVP bar (text-first)
Pull a time-window of brain events and produce a written recap "episode" (script +
storyboard) — runnable before any video rendering exists.

## Next steps (execute in order)
1. **Brain event reader** — query `memory_events` + session `summary_short` for a time
   window; build a compact, token-budgeted context bundle (cast = the five agents).
2. **Scriptwriter** — `qwen-plus` turns the bundle into a short script + storyboard;
   keep the prompt lean to showcase the token-budget discipline.
3. **Journaling MVP** — emit a markdown recap of "what the society did" → doubles as
   blog-post material. Wire this up **early** so it documents the build as we go.
4. **Episode registry** — record episodes in `showrunner.private`.
5. **Video render (polish)** — feed the storyboard to Wan / HappyHorse to generate
   clips; auto-edit into a <90s short. (Deferred until the text path works.)
6. Deploy on Alibaba Cloud + proof; diagram; `HACKATHON.md`; the episode itself is the
   demo.

## Dependencies
- Brain `memory_events` populated (other agents writing events makes richer episodes).
- DashScope `qwen-plus`; later Wan/HappyHorse video access.

## Definition of done
- [ ] Reads brain events under a token budget → script/storyboard via Qwen
- [ ] Text recap/journaling works (blog-post material)
- [ ] Episode registry in `showrunner.private`
- [ ] (Polish) video render → <90s short
- [ ] Deployed on Alibaba Cloud + proof; diagram + `HACKATHON.md`
