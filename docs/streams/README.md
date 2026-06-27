# Stream plans — pick one and go

Each file here is a **loop-ready plan** for one stream of the Qwen Agent Collective.
A local Qwen loop (or any contributor) can open a single stream doc and execute its
**Next steps** checklist top-to-bottom without needing the rest of the context.

All five agents share one **brain** (the memory substrate). Build order is
dependency-first: the brain ships before the agents that read it.

| Stream | Track | Tier | Depends on | Doc |
|--------|-------|------|-----------|-----|
| Brain (substrate) | 1 — infra for all | core | — | [brain.md](brain.md) |
| Memory / Echo | 1 — MemoryAgent | core | brain | [memory-echo.md](memory-echo.md) |
| GIT-Committer | 3 — Agent Society | core | brain | [git-committer.md](git-committer.md) |
| Open-Translate | 4 — Autopilot | core | brain | [open-translate.md](open-translate.md) |
| Skippy concierge | 5 — EdgeAgent | stretch | brain | [skippy-concierge.md](skippy-concierge.md) |
| Showrunner | 2 — AI Showrunner | stretch | brain + events | [showrunner.md](showrunner.md) |

**Global pass/fail (every stream):** Qwen models must run on Alibaba Cloud Model
Studio (DashScope) — not local Ollama; public repo + OSS license; architecture
diagram; proof of Alibaba Cloud deployment; <3-min demo video; `HACKATHON.md`
significant-updates log (2026-05-26 → 2026-07-09).

**Shared env (DashScope):** `DASHSCOPE_API_KEY`, `DASHSCOPE_BASE_URL`, model ids
`qwen-plus`, `qwen2.5-coder-32b-instruct`, `qwen-vl-max`, `qwen2-audio-instruct`,
`text-embedding-v3`. See `/.env.example`.

**Namespace contract:** only the owning agent writes its own `<agent>.private`; all
agents read any `shared.*`; writes to `shared.*` go through `memory_review_queue`.
