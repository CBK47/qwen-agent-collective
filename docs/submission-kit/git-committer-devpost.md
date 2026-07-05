# Devpost Draft: Track 3 Agent Society

## Project Name

git-committer: A Debating Society for Your Diffs

## Track

Track 3: Agent Society

## Short Description

A Qwen-powered code-review council. Three specialist reviewers work the same
diff in parallel, debate each other's findings in a rebuttal round, then a
negotiator merges the survivors into one verdict plus a Conventional Commits
message — and proves its worth with a deduplicated delta against a
single-agent baseline.

## What It Does

Developers paste or pipe a unified diff into `git-committer`. The pipeline is
the Track 3 brief made literal — task division, dialogue, negotiation:

1. **Task division** — correctness, security, and style/test reviewers (each a
   Qwen call with a disjoint lane) review the same diff in parallel.
2. **Dialogue** — a debate round: each reviewer sees its peers' findings and
   revises its own, conceding duplicates, defending disputed calls, or adding
   what the discussion surfaced. Each reports a one-line stance
   ("defended the negative-percent bug; conceded the secret to security").
3. **Negotiation** — a reconciliation agent dedupes and ranks the post-debate
   findings into one verdict and writes the Conventional Commits message.
4. **Proof** — a single-agent baseline reviews the same diff. The metric
   compares *deduplicated* team findings against the baseline, so the society
   must win on distinct issues, not volume.

## Built With

- Qwen via Alibaba Cloud Model Studio / DashScope (`qwen3-coder-plus`)
- Python CLI pipeline (`agents/git-committer/review.py`), parallel reviewer
  fan-out via `ThreadPoolExecutor`
- Strict JSON contracts between agents, fence-tolerant parsing
- Shared brain conventions from `shared/code_conventions.py`
- Node.js zero-dependency WebUI + API bridge (`webui/server.mjs`)
- Alibaba Cloud ECS deployment (`agents/git-committer/deploy.py`)

## Key Features

- Role-specialized reviewers with explicitly disjoint lanes
- A real dialogue step: reviewers cross-examine each other and change their
  positions — visible in the output as per-role stances
- Negotiated verdict plus an auto-written Conventional Commits message
- Honest Agent Society metric: `team_issue_count` is deduplicated post-debate,
  with `first_pass_issue_count` and `baseline_issue_count` alongside for
  transparency
- WebUI endpoint at `/api/git-committer` for the live demo
- ECS deployment script that keeps secrets out of user-data

## Case Study: The Society Caught a Frontier Model's Bug

During development, the pipeline reviewed its own diff — code written by a
frontier coding model (Claude Fable 5). The Qwen reviewer society flagged the
JSON extraction as fragile: it grabbed first-`{` to last-`}`, which breaks
when a response contains multiple JSON-looking fragments. The bug was not
hypothetical — it was manifesting **in that very run**, silently dropping the
panel's own first-pass findings. The single-agent baseline found **zero**
issues on the same diff.

The fix and regression tests are commit `2adc3d9` in the repo history.

The panel then alleged a "critical" escaped-quote bug in the fix. A regression
test disproved it. That is the intended workflow: panel findings are claims,
tests are verdicts — the society surfaces more issues than one reviewer, and
verification filters the false positives.

## Demo Script (~3 min)

1. Open `webui/git-committer.html`; paste `agents/git-committer/sample.patch`
   — it hides a live Stripe key, a negative-discount logic bug, and a removed
   refund guard.
2. Run review. Walk the output top to bottom: first-pass findings per role →
   the debate round (who conceded, who defended) → the negotiated verdict →
   the suggested commit message.
3. Land on the delta metric: the deduplicated team count vs the single-agent
   baseline over the same diff.
4. The case study: `git show 2adc3d9` — the society reviewed its own diff,
   caught a real parser bug a frontier coding model (Claude Fable 5) wrote and
   missed, while the single-agent baseline found nothing. Then the honesty
   beat: the panel's follow-up "critical" finding was disproven by a test —
   claims get verified, not trusted.
5. Show the architecture diagram and the ECS deployment.

## Commands For Judges

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
make test PYTHON=.venv/bin/python
node webui/server.mjs   # then open http://localhost:4321/git-committer.html
```

With `DASHSCOPE_API_KEY` set, run:

```bash
python agents/git-committer/review.py --diff-file agents/git-committer/sample.patch --format text
```

## What To Submit

- Code repo: `https://github.com/CBK47/qwen-agent-collective`
- Track: Track 3: Agent Society
- Architecture diagram: `docs/architecture/git-committer-track3.md`
- Alibaba Cloud deployment proof: recording of the WebUI served from ECS
  (deployed via `agents/git-committer/deploy.py`)
- Demo page: deployed ECS URL, or local `http://localhost:4321/git-committer.html`
- Video: ~3 minute walkthrough following the demo script above
