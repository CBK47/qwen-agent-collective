# Hackathon Submission Log

Global AI Hackathon with Qwen Cloud — submissions close **2026-07-08/09, 2pm PT**.
One shared brain + five specialist Qwen agents on DashScope.
**Build law:** breadth-first — five thin *demoable* agents beat one gold-plated one.

---

## PM Status Board — SSOT

Refresh this table every PM session. Last refresh: **2026-07-02** (~6 working days left). Loops PAUSED; prod-readiness review complete → see `REVIEW.md`.
STATE ∈ not-started · in-progress · blocked · done. OWNER-CHAT = the code chat that does NEXT ACTION.

| Track / Layer | STATE | LAST DECISION | NEXT ACTION (one step) | OWNER-CHAT |
|---|---|---|---|---|
| Spine `shared/` | **done** | DashScope Singapore compatible endpoint; chat + embeddings live, smoke passes | Frozen — agents import, never fork | — |
| **Brain runtime** ⭐ keystone | **done** | `shared/brain.py` E2E verified: ingest→retrieve, Postgres+Qdrant, governance, token budget | — | — |
| T1 · memory-echo | **in-progress** | `session_logger.py` + `brain/demo/track1_demo.py` work; WebUI renders | Fix cwd-relative import in demo; wire `/api/memory-echo` properly | chat:memory-echo |
| T2 · showrunner | **in-progress** | `recap.py` imports OK (needs brain live); broken duplicates `main.py`/`script_generator.py` exist | Delete broken duplicates; confirm recap.py runs end-to-end against live brain | chat:showrunner |
| T3 · git-committer | **demo-ready** | Debate round added (task division → dialogue → negotiation), honest deduped delta, Conventional Commit output, `sample.patch`, WebUI verified E2E in browser, 34/34 tests | Deploy to ECS + record ~3 min video | chat:git-committer |
| T4 · open-translate | **in-progress** | `translate.py` CLI verified (`--help` OK); broken duplicate `translator.py` exists | Delete `translator.py`; wire `/api/open-translate` endpoint | chat:open-translate |
| T5 · skippy-concierge | **blocked** | `device_handler.py` broken (`from app import db`); `skippy_demo.py` broken (dashed pkg); no working entrypoint | Write a real single-file `skippy.py` (text→action via BrainClient, no `app`, no dashes) | chat:skippy |
| Deploy + proof (×5 required) | **not-started** | `deploy.py` files all fail — missing `aliyunsdkcore`/`oss2` SDKs; **0/5 deployed** | Decision needed: genuinely deploy on Alibaba Cloud, OR pivot to honest local-first story | chat:infra |
| Submission kit | **in-progress** | Blogger + `blog.html` + `viewer.html` exist; videos not recorded yet | Record 5 videos once per-track demos run end-to-end | chat:submission |

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
| 2026-07-02 | **Loops PAUSED** — paused all 3 n8n coding-agent workflows (incl. 2 unguarded ones that were the root cause of keystone churn). Deep prod-readiness review → `REVIEW.md`. Reconciled all PLAN.md/HACKATHON.md checkboxes to reality. 0/5 deployed, 0/5 videos. Working: keystone, git-committer, translate.py CLI, T1 demo, WebUIs render. Blocked: skippy (no working entrypoint). |
| 2026-07-05 | **Decision — all-in on T3.** git-committer polished to submission grade: debate/rebuttal round makes the Track 3 "dialogue" criterion literal; delta metric now counts **deduplicated** post-negotiation issues (was raw per-role sum — duplicate-inflated); negotiator writes the Conventional Commit message (name promise fulfilled); `sample.patch` added (docs referenced a file that didn't exist); JSON fence-tolerant parsing; role reviewers parallelized; WebUI 404 fixed (dead path-rewrite); test FakeClient repaired (last commit broke `make test`); live E2E verified in browser — delta +1 on sample.patch. |
| _ongoing_ | Log real milestones here through 2026-07-09. |

---

## Per-track submission proofs (required for each track)

**Status as of 2026-07-02: 0/5 deployed, 0/5 videos recorded.**

| Track | Agent | Deployment Proof | Demo Video |
|---|---|---|---|
| T1 MemoryAgent | memory-echo | NOT DEPLOYED — local only | NOT RECORDED |
| T2 AI Showrunner | showrunner | NOT DEPLOYED — local only | NOT RECORDED |
| T3 Agent Society | git-committer | NOT DEPLOYED — local only | NOT RECORDED |
| T4 Autopilot | open-translate | NOT DEPLOYED — local only | NOT RECORDED |
| T5 EdgeAgent | skippy-concierge | NOT DEPLOYED — local only | NOT RECORDED |
| Blog Post Award | submission-kit (`blogger.py`, `blog.html`, `viewer.html`) | n/a | n/a |
