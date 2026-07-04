# Track 3 Architecture: git-committer Agent Society

`git-committer` is the Track 3 submission path for the Qwen Cloud hackathon.
It turns a unified diff into a negotiated code-review verdict plus a
Conventional Commits message by running three specialist Qwen reviewers, a
debate round, and a negotiation step, then comparing the team result with a
single-agent baseline.

## Agent Roles

| Role | Responsibility | Output |
|---|---|---|
| Correctness reviewer | Logic bugs, edge cases, behavioral regressions | JSON issue list |
| Security reviewer | Secrets, injection, auth gaps, unsafe data handling | JSON issue list |
| Style/test reviewer | Maintainability, naming, dead code, missing tests | JSON issue list |
| Debate round (all three) | Each reviewer sees peers' findings; concedes, defends, or adds | Revised issue list + stance |
| Negotiator | Deduplicate, rank severity, resolve conflicts, write commit message | Final verdict JSON |
| Baseline reviewer | Single-pass holistic review for comparison | JSON issue list |

## Data Flow

```mermaid
flowchart LR
    User[Developer or judge] --> WebUI[webui/git-committer.html]
    WebUI --> API[POST /api/git-committer]
    API --> CLI[agents/git-committer/review.py]
    CLI --> Brain[shared BrainClient]
    Brain --> Conventions[shared/code_conventions.py]
    CLI --> C[Qwen correctness reviewer]
    CLI --> S[Qwen security reviewer]
    CLI --> T[Qwen style/test reviewer]
    C --> D[Debate round: peers' findings cross-examined]
    S --> D
    T --> D
    D --> N[Qwen negotiation: verdict + commit message]
    CLI --> B[Qwen single-agent baseline]
    N --> Metric[Agent Society delta metric]
    B --> Metric
    Metric --> API
    API --> WebUI
```

## Why This Fits Track 3

The track brief asks for agents that collaborate through *task division,
dialogue, and negotiation* — this pipeline has all three as explicit, separate
steps:

- **Task division**: three role reviewers with disjoint lanes run in parallel.
- **Dialogue**: a rebuttal round where each reviewer reads its peers' findings
  and revises its own — conceding duplicates, defending disputed calls, adding
  what the discussion surfaced. Each reviewer reports a one-line `stance`.
- **Negotiation**: a reconciliation agent merges the post-debate findings into
  one verdict and a Conventional Commits message.

The `metric.delta` field compares **deduplicated** team issue discovery
against a single-agent baseline over the same diff, so the society has to beat
the baseline on distinct findings, not volume.

## Runtime Entry Points

```bash
# CLI: JSON output for judging and tests
python agents/git-committer/review.py --diff-file agents/git-committer/sample.patch

# CLI: text output for demos
git diff HEAD~1 | python agents/git-committer/review.py --format text

# Web UI
node webui/server.mjs
# open http://localhost:4321/git-committer.html
```

## Alibaba Cloud Deployment Proof

The deployment proof file is `agents/git-committer/deploy.py`. It uses Alibaba
Cloud ECS SDK calls to create and start an instance, then user-data installs the
repo and starts `webui/server.mjs` as a systemd service. The DashScope key is
not placed in user-data; the instance reads it from
`/etc/qwen-agent-collective.env`.

Dry-run proof command:

```bash
python agents/git-committer/deploy.py --dry-run
```

Real deploy requires:

```bash
export ALIBABA_CLOUD_ACCESS_KEY_ID=...
export ALIBABA_CLOUD_ACCESS_KEY_SECRET=...
export ALIBABA_CLOUD_REGION=cn-hangzhou
export ALIYUN_ZONE_ID=...
export ALIYUN_SECURITY_GROUP_ID=...
export ALIYUN_VSWITCH_ID=...
export ALIYUN_IMAGE_ID=...
python agents/git-committer/deploy.py
```
