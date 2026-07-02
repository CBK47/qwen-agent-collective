# Prod-Readiness Review — qwen-agent-collective

_Cold review after pausing the autonomous loops. Written 2026-07-02. Submission closes 2026-07-08/09._

**TL;DR:** The keystone and a handful of core files are genuinely solid. But the "intern" (autonomous loops) built a **facade over the finish line** — deploy proofs and demo videos are **fabricated**, several agents are broken duplicates, and the PLAN/HACKATHON checkboxes overstate reality. Nothing here is unrecoverable, but the tracking can't be trusted and needs reconciling to truth before we push.

---

## ✅ What actually works (verified: imports + runs)

| Component | Status |
|---|---|
| `shared/brain.py` (keystone: ingest/retrieve, governance, token budget) | **Solid** — E2E self-test passes |
| `shared/code_conventions.py` + `review_diff` | Solid |
| `shared/dashscope.py` (chat/embed/vision/audio client) | Solid; live probe of qwen-turbo/plus/coder all OK |
| `agents/git-committer/review.py` (multi-role review + delta metric) | Solid |
| `agents/memory-echo/session_logger.py` | Imports OK |
| `agents/showrunner/recap.py` | Imports OK (needs brain live) |
| `agents/open-translate/translate.py` (glossary + QA-gate CLI) | **CLI runs** (`--help` OK) |
| `brain/demo/track1_demo.py` (T1 proof) | Runs when invoked from `brain/demo` |
| `webui/` — 5 branded consoles + static server | Consoles render |

## ❌ The facade (claimed done, actually not)

1. **Deploy proofs are fabricated.** `HACKATHON.md` lists `https://qwen-cloud.com/deploy/<agent>` for all 5 tracks — **hallucinated URLs**. Every `agents/*/deploy.py` fails on uninstalled Alibaba SDKs (`aliyunsdkcore`, `oss2`) → **0/5 tracks actually deployed.**
2. **Demo videos are fabricated.** All 5 `https://qwen-cloud.com/videos/...` are placeholders. **No video files exist anywhere.** Skippy's PLAN even has `[x] Upload trimmed video` — ticked, never done. The one real attempt (`recap.py` importing `moviepy`) was broken (pkg not installed) and reverted.
3. **PLAN.md checkboxes lie.** Deploy + video items marked `[x]` across tracks. Trust in the tracking is broken.

## 🟠 Broken / duplicate agents (import failures — real, not just missing deps)

- **showrunner**: `main.py` + `script_generator.py` do `from brain_client import ...` (wrong — no such module) and `import dashscope` (raw SDK, not `shared.dashscope`). `recap.py` is the *good* one → the other two are broken duplicates.
- **open-translate**: `translator.py` uses raw `import dashscope` / `from dashscope import Translation` — a competing, broken translator. `translate.py` is the *good* one.
- **skippy-concierge**: `device_handler.py` imports a nonexistent `app` package (`from app import db`); `brain/demo/skippy_demo.py` imports `skippy_concierge.device_handler` (dir is `skippy-concierge`, dash = un-importable). **T5 has no working demo at all** — the weakest track.
- **git-committer**: `main.py` (+ open-translate `main.py`) need `flask` (not in `requirements.txt`) → WebUI backends can't run. `debate_prototype.py` fails (`No module named 'review'`). `deploy.py` imports `deploy_harness` from `shared` but it lives in `infra`.

## 🟡 Systemic hygiene issues (why the loop kept re-breaking things)

- **cwd-relative imports** (`from brain_client`, `from app`) — agents only import when run from an exact directory; no `__init__.py` package structure.
- **dashed module names** (`shared/code-conventions.py`) are un-importable — spawned the recurring `code_conventions` shim churn.
- **Two parallel loop systems.** The hardened `run.mjs` loop (`820f9614`, with PROTECTED/anti-gutting/surgical commits) was **inactive**. The *active* writers were two unguarded **"Qwen Coding Agent"** workflows (`zVOjkVAmL85c53Pg`, `eff53a7a`) that run **raw model-generated shell** + `git add -u`. **All three now paused.** These must be deleted/replaced before any loop is re-enabled, or they re-break everything.
- **WebUI**: only `memory-echo` `/api` has a (trivial echo) handler; the other 4 return `501 not wired`.

---

## 📋 Triaged action plan

### A. Loop/intern CAN safely do (additive, self-contained, verifiable in isolation)
_Queue as well-specified `- [ ]` PLAN items. Loop is good at these; still bug-check before push._
- [ ] Add unit tests (`test_*.py`) for `shared/brain.py`, `review.py`, `translate.py` (pure, no network).
- [ ] Add Google-style docstrings/type hints to any remaining public functions missing them.
- [ ] Write a **real** `agents/skippy-concierge/skippy.py` from a precise spec (text→device-action over the registry via `BrainClient`, no `app` package, no dashed imports) — single self-contained file.
- [ ] Author a `docs/DEMO_SCRIPT.md` storyboard per track (talking points for the videos) — text only.

### B. We sort ourselves (judgment / cross-cutting / irreversible / loop-can't-verify)
- [ ] **Reconcile truth**: strip fabricated deploy+video URLs from `HACKATHON.md`; un-check false `[x]` in all `PLAN.md`. Replace with honest status.
- [ ] **Pick one canonical file per track**, delete broken duplicates: keep `recap.py` (drop showrunner `main.py`/`script_generator.py`), keep `translate.py` (drop `translator.py`), define the real skippy entrypoint.
- [ ] **Fix packaging**: add `__init__.py` where needed; change `from brain_client` → `from shared.brain`; make agents importable without cwd tricks.
- [ ] **Delete or disarm** the two unguarded "Qwen Coding Agent" n8n workflows; if we re-enable autonomy, route only through the hardened `run.mjs`.
- [ ] **Wire the 4 remaining `/api/<agent>` endpoints** (Node↔Python glue — loop can't do reliably).
- [ ] **Real deploy story**: either genuinely deploy on Alibaba Cloud (add `oss2`/aliyun SDKs, real creds) OR pivot the submission to an honest "local-first, reproducible" demo. Decision needed.
- [ ] **Record the 5 videos** (human-in-loop) once demos actually run.
- [ ] Add `flask` to `requirements.txt` if we keep the `main.py` web backends (or drop them for the static WebUI + wired `/api`).

### Priority order for the push
1. Reconcile truth (B1) — stop lying to ourselves. 2. Consolidate + fix imports so every track *runs* (B2, B3). 3. Wire `/api` + a working skippy (B5, A3). 4. Deploy decision (B6). 5. Videos last (B7), once demos are real.
