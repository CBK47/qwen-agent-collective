# Devpost Draft: Track 3 Agent Society

## Project Name

Qwen Agent Collective: git-committer Code Review Council

## Track

Track 3: Agent Society

## Short Description

A Qwen-powered multi-agent code review council that splits a diff across
correctness, security, and style/test reviewers, negotiates one final verdict,
and reports a measurable delta against a single-agent baseline.

## What It Does

Developers paste or pipe a unified diff into `git-committer`. Three specialist
Qwen reviewer agents inspect the same change from different angles. A fourth
Qwen negotiation step deduplicates and ranks their findings into one final
verdict. The system then runs a single-agent baseline over the same diff and
reports whether the agent society found more issues than the baseline.

## Built With

- Qwen via Alibaba Cloud Model Studio / DashScope
- `QWEN_CODER_MODEL` for role reviews and negotiation
- Python CLI for the review pipeline
- Node.js static WebUI and API bridge
- Shared brain conventions from `shared/code_conventions.py`
- Alibaba Cloud ECS deployment script in `agents/git-committer/deploy.py`

## Key Features

- Role-specialized reviewers: correctness, security, style/test coverage
- Strict JSON model contracts for machine-checkable reviewer output
- Negotiation step that resolves overlapping findings into one verdict
- Single-agent baseline comparison with `team_issue_count`,
  `baseline_issue_count`, and `delta`
- WebUI endpoint at `/api/git-committer` for demo and deployment
- Alibaba Cloud ECS deployment proof script with no secrets in user-data

## Demo Script

1. Show the repo root, license, and Track 3 architecture file.
2. Start the UI with `node webui/server.mjs`.
3. Open `http://localhost:4321/git-committer.html`.
4. Paste a diff containing a hardcoded secret and a weak edge-case branch.
5. Run review and show the correctness/security/style findings.
6. Point out the negotiation verdict and Agent Society delta metric.
7. Show `agents/git-committer/deploy.py --dry-run` as deployment proof code.
8. End on the architecture diagram and explain how the same server runs on ECS.

## Commands For Judges

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
make test PYTHON=.venv/bin/python
node webui/server.mjs
```

With `DASHSCOPE_API_KEY` set, run:

```bash
git diff HEAD~1 | python agents/git-committer/review.py --format text
```

## What To Submit

- Code repo: `https://github.com/CBK47/qwen-agent-collective`
- Track: Track 3: Agent Society
- Architecture diagram: `docs/architecture/git-committer-track3.md`
- Alibaba Cloud proof code: `agents/git-committer/deploy.py`
- Demo page: deployed ECS URL, or local `http://localhost:4321/git-committer.html`
- Video: 3 minute walkthrough following the demo script above
