# Kickoff Roadmap

Breadth-first MVP for the **Global AI Hackathon with Qwen Cloud** (submissions close
**2026-07-09, 2pm PT**). One shared **brain** + five specialist Qwen agents, all calling
Qwen on **Alibaba Cloud Model Studio (DashScope)** at runtime.

This file is the single starting point when you sit down at your Mac.

## Done (this planning pass)
- `brain/db/postgres-init.sql` — full schema + 5-agent/`shared` + `connor` seed.
- `brain/.env.example` — DashScope (compatible-mode) + Postgres/Qdrant/n8n; root `.env.example` reconciled.
- `brain/memory-manifest.yaml` — namespace access contract + Qdrant collections (dim 1024).
- `brain/orchestrator/PORT-PLAN.md` — Ollama→DashScope port plan + checklist.
- `agents/<name>/PLAN.md` — uniform kickoff plan for all five agents.

## Pending (your Mac follow-ups, in order)
1. **Finish the brain orchestrator** — copy the real `n8n-memory-orchestrator.json`
   from `CBK47/Agents@claude/qwen-hackathon-ideas-bs1z60`, apply the 3-node DashScope
   port (`brain/orchestrator/PORT-PLAN.md`).
2. **Stand up the stack** — `brain/docker-compose.yml` (postgres + qdrant + n8n); fill
   `DASHSCOPE_API_KEY`; create Qdrant collections.
3. **Track-1 demo harness** — ingest → forget stale → recall under a tight context budget.
4. **Five agent MVPs** — each: one real DashScope call + one brain read/write (see PLANs).
5. **Alibaba Cloud deploy + proof** — ECS or Function Compute; save a deployment-proof file.
6. **Submission kit** — architecture diagram (`docs/architecture/`), <3-min demo video,
   `HACKATHON.md` updates through 2026-07-09.

## Pass/fail submission checklist (per track)
- [ ] Qwen models run on DashScope / Alibaba Cloud Model Studio (NOT local Ollama)
- [ ] Public repo + OSS license (MIT — present)
- [ ] Architecture diagram
- [ ] Proof of Alibaba Cloud deployment
- [ ] <3-min demo video
- [ ] `HACKATHON.md` significant-updates log (2026-05-26 → 2026-07-09)

## Notes / blockers carried from the web session
- `CBK47/Agents` was **not reachable** here (GitHub scope locked to this repo), so the
  brain files were rebuilt from the pasted spec and the 20 KB n8n JSON is left for the Mac.
- No live DashScope or Alibaba Cloud calls were made — those need your `DASHSCOPE_API_KEY`
  and cloud credentials.
