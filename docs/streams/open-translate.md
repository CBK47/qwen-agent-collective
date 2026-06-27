# Stream: Open-Translate

- **Track:** 4 (Autopilot)
- **Tier:** core
- **Goal:** an end-to-end localization workflow — ingest a doc → translate → enforce
  glossary/term consistency via persistent translation memory (the brain) →
  QA/back-translation gate → human-in-the-loop checkpoint on low-confidence segments →
  publish.
- **Why Qwen:** `qwen-plus` multilingual translation + QA reasoning on DashScope.
- **Brain namespace:** reads/writes `shared.glossary`; writes `open-translate.private`.

## Current state
- Not started. Lives at `agents/open-translate/` in `qwen-agent-collective`.

## MVP bar
Feed a document, get a translated output where glossary terms are consistent, low-
confidence segments are flagged for human review, and a QA gate ran.

## Next steps (execute in order)
1. **Scaffold** `agents/open-translate/`: ingest a doc (md/txt), segment it.
2. **Translate** each segment with `qwen-plus`; capture a per-segment confidence.
3. **Glossary / translation memory** — before translating, look up terms in
   `shared.glossary` (brain `retrieve`); after approval, write new term pairs back
   (brain `ingest` → review queue). This persistent TM is the differentiator.
4. **QA gate** — back-translate and compare (or LLM-judge) to catch drift; mark
   segments pass/needs-review.
5. **HITL checkpoint** — pause on low-confidence / failed-QA segments for human
   approval, then continue. (Show ambiguous-input handling here.)
6. **Publish** the assembled translated document.
7. Deploy on Alibaba Cloud + proof; diagram; `HACKATHON.md`; demo: doc → translate →
   QA → checkpoint → published output.

## Dependencies
- Brain (for `shared.glossary` TM) — can stub the glossary store and wire later.
- DashScope key + `qwen-plus`.

## Definition of done
- [ ] End-to-end doc → published translation
- [ ] Glossary consistency via persistent TM in the brain
- [ ] QA/back-translation gate + HITL checkpoint working
- [ ] Deployed on Alibaba Cloud + proof
- [ ] Diagram + `HACKATHON.md` + demo video
