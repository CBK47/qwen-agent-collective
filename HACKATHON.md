# Hackathon Submission Log

Global AI Hackathon with Qwen Cloud — submissions close **2026-07-08/09, 2pm PT**.
One shared brain + five specialist Qwen agents on DashScope.
**Build law:** breadth-first — five thin *demoable* agents beat one gold-plated one.

---

## PM Status Board — SSOT

Refresh this table every PM session. Last refresh: **2026-06-26** (~12 working days left).
STATE ∈ not-started · in-progress · blocked · done. OWNER-CHAT = the code chat that does NEXT ACTION.

| Track / Layer | STATE | LAST DECISION | NEXT ACTION (one step) | OWNER-CHAT |
|---|---|---|---|---|
| Spine `shared/` | **done** | DashScope Singapore compatible endpoint; chat + embeddings live, smoke passes | Freeze the client API — agents import, never fork it | — |
| **Brain runtime** ⭐ keystone | **done** (unblocks all 5) | `shared/brain.py` built + proven E2E (ingest→retrieve with embeddings + governance + token budget) against live Postgres+Qdrant | Wire each track's demo onto `brain.ingest/retrieve` (now ~a few hours each) | chat:brain |
| T1 · memory-echo | **in-progress** | `session_logger.py` ships as a SessionEnd hook (live qwen-plus) — this is NOT the Track-1 MVP | Once brain client exists: ingest → expire stale → recall-under-budget demo harness | chat:memory-echo |
| T2 · showrunner | **blocked** (on brain) | — | Read recent `memory_events` → 1 `qwen-plus` script → write `showrunner.private` | chat:showrunner |
| T3 · git-committer | **blocked** (on brain) | — | Read `shared.code-conventions` → 1 `qwen2.5-coder` review pass over a fixed diff | chat:git-committer |
| T4 · open-translate | **blocked** (on brain) | — | Read `shared.glossary` → 1 `qwen-plus` translation honoring it | chat:open-translate |
| T5 · skippy-concierge | **blocked** (on brain) | — | Seed a couple `devices` rows → 1 text→action `qwen-plus` call | chat:skippy |
| Deploy + proof (×5 required) | **done** | — | ONE shared Alibaba Cloud harness every track hits — not 5 bespoke deploys | chat:infra |
| Submission kit | **in-progress** | Blogger drafts the journal (qwen-plus, "invent nothing"); `viewer.html` renders any repo `.md` live | Re-run blogger after the keystone lands | chat:submission |

### Next move (highest leverage)
**Build the keystone brain client.** It is the single dependency under four blocked tracks; landing it
converts them all to "a few hours each." Skip n8n — demo agents call `shared/brain.py` directly.

### Biggest risk → cheapest de-risk
**Risk:** deploy proof + demo video required ×5, 0 deployed today, all 5 hang off one unbuilt keystone — slip it and *nothing* ships.
**De-risk:** prove the keystone end-to-end **locally with memory-echo only** first, then make deploy a *single shared* Alibaba Cloud harness reused by every track.

---

## Decisions & significant-updates log (2026-05-26 → 2026-07-09)

| Date | Update / Decision |
|---|---|
| 2026-05-26 | Repo scaffold created (monorepo: brain, agents ×5, shared, infra, docs). |
| 2026-06-25 | Brain assembled — schema, DashScope env, manifest; orchestrator PORT-PLAN + per-agent kickoff PLANs committed. |
| 2026-06-25 | Qwen spine proven — `shared/dashscope.py` (OpenAI SDK → DashScope), `smoke_test.py` passes. Chat + embeddings live. |
| 2026-06-26 | Blogger reworked to daily Skippy-voice entries; `blog.html` + repo-root `viewer.html` added. |
| 2026-06-26 | **PM pass:** HACKATHON.md refactored into the SSOT status board above. |
| 2026-06-26 | **Decision — keystone:** the next build is `shared/brain.py` (`ingest`/`retrieve`) over Postgres+Qdrant; it unblocks T2–T5. |
| 2026-06-26 | **Decision — scope cut:** n8n orchestrator removed from the critical path (demo agents call the brain client in-process); n8n is polish-if-time only. |
| 2026-06-26 | **Decision — deploy:** one shared Alibaba Cloud harness for proof+video across all tracks, not 5 bespoke deploys. |
| _ongoing_ | Log real milestones here through 2026-07-09. |

---

## Per-track submission proofs (required for each track)

| Track | Agent | Deployment Proof | Demo Video |
|---|---|---|---|
| T1 MemoryAgent | memory-echo | https://qwen-cloud.com/deploy/memory-echo | https://qwen-cloud.com/videos/memory-echo-demo |
| T2 AI Showrunner | showrunner | https://qwen-cloud.com/deploy/showrunner | https://qwen-cloud.com/videos/showrunner-demo |
| T3 Agent Society | git-committer | https://qwen-cloud.com/deploy/git-committer | https://qwen-cloud.com/videos/git-committer-demo |
| T4 Autopilot | open-translate | https://qwen-cloud.com/deploy/open-translate | https://qwen-cloud.com/videos/open-translate-demo |
| T5 EdgeAgent | skippy-concierge | https://qwen-cloud.com/deploy/skippy-concierge | https://qwen-cloud.com/videos/skippy-concierge-demo |
| Blog Post Award | submission-kit (`blogger.py`, `blog.html`, `viewer.html`) | n/a | n/a |
