# Stream: GIT-Committer

- **Track:** 3 (Agent Society)
- **Tier:** core
- **Goal:** a team of specialist review agents (correctness, security, style,
  test-coverage) split a PR, review in parallel, surface disagreements, and negotiate
  a single verdict — beating a single-agent baseline by a measurable margin.
- **Why Qwen:** `qwen2.5-coder-32b-instruct` on DashScope — strong + cheap at review.
- **Brain namespace:** writes `git-committer.private`; reads/writes
  `shared.code-conventions` (via review queue).

## Current state
- Not started. Lives at `agents/git-committer/` in `qwen-agent-collective`.
- Brain + namespace contract available.

## MVP bar
Given a PR diff, ≥3 role-agents produce findings, a negotiation step merges them into
one verdict, and the run prints a metric vs a single-agent baseline.

## Next steps (execute in order)
1. **Scaffold** `agents/git-committer/`: a runner that takes a PR/diff as input.
2. **Role agents** — implement ≥3 (correctness, security, style/test-coverage), each a
   `qwen2.5-coder` call with a role-specific system prompt (`prompts/git-committer/`).
3. **Parallel review** — fan out the diff (or hunks) to the roles; collect findings.
4. **Negotiation** — a reconciliation step that surfaces disagreements and produces one
   ranked verdict (accept / request-changes + prioritized issues).
5. **Baseline + metric** — run a single `qwen2.5-coder` reviewer over the same PR;
   compare (bugs caught / false-positive rate / time). This delta is the Track-3 story.
6. **Persist conventions** — write agreed style/standards to `shared.code-conventions`
   so future reviews stay consistent.
7. Deploy on Alibaba Cloud + proof; diagram; `HACKATHON.md`; demo: PR → split →
   disagree → verdict → metric vs baseline.

## Dependencies
- Brain (for `shared.code-conventions`) — can start with a stub and wire later.
- DashScope key + `qwen2.5-coder` access.

## Definition of done
- [ ] ≥3 role agents + negotiation producing one verdict
- [ ] Measurable gain over single-agent baseline (documented)
- [ ] Conventions persisted to `shared.code-conventions`
- [ ] Deployed on Alibaba Cloud + proof
- [ ] Diagram + `HACKATHON.md` + demo video
