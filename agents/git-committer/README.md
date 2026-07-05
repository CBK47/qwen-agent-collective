# git-committer

**Track:** Track 3 - Agent Society

## Purpose

Reviews diffs through a society of specialist Qwen reviewers and writes a
Conventional Commits message, following shared code conventions from the brain.
The pipeline is task division → dialogue → negotiation: three role reviewers
work the same diff in parallel, debate each other's findings in a rebuttal
round, then a negotiator merges the surviving findings into one verdict and a
suggested commit message.

## Setup

To use the git-committer agent with DashScope, follow these steps:

1. **Install dependencies**:

   ```
   pip install -r requirements.txt
   ```

2. **Obtain API Key**: Log in to the [DashScope console](https://dashscope.console.aliyun.com/) and navigate to the API Key section to generate or retrieve your API key.

3. **Create .env File**: In the root directory of the project, create a `.env` file if it doesn't already exist.

4. **Set API Key**: Add the following line to the `.env` file, replacing `your_api_key_here` with your actual DashScope API key:
   ```
   DASHSCOPE_API_KEY=your_api_key_here
   ```

## Running the Track 3 Demo

The canonical implementation is `review.py`. It runs three role-specific Qwen
reviewers in parallel, a rebuttal round where each reviewer revises its
findings against its peers', a Qwen negotiation step that produces the verdict
and commit message, and a single-agent baseline over the same diff.

```bash
# JSON output for judging (sample.patch ships with the repo)
python agents/git-committer/review.py --diff-file agents/git-committer/sample.patch

# Human-readable demo output
git diff HEAD~1 | python agents/git-committer/review.py --format text
```

Start the WebUI from the repository root:

```bash
node webui/server.mjs
```

Then open `http://localhost:4321/git-committer.html`. The page posts to
`/api/git-committer`, which invokes `review.py` and returns the negotiated
review report.

## Agent Society Metric

The result includes:

- `team_issue_count`: **deduplicated** issues surviving debate + negotiation —
  three reviewers flagging the same secret count once
- `first_pass_issue_count`: raw per-role findings before the debate round
- `baseline_issue_count`: issues found by one holistic reviewer over the same diff
- `delta`: `team_issue_count - baseline_issue_count`

This gives the Track 3 submission an honest, measurable comparison between the
multi-agent society and a single-agent baseline: the delta only counts distinct
issues the team surfaced, not the same issue echoed by three roles.

## Alibaba Cloud Deployment

`deploy.py` creates an Alibaba Cloud ECS instance and installs the WebUI service
through ECS user-data. It deliberately does not embed `DASHSCOPE_API_KEY` in
user-data; put secrets in `/etc/qwen-agent-collective.env` on the instance.

```bash
python agents/git-committer/deploy.py --dry-run
```

For real deployment, set the required `ALIBABA_CLOUD_*` and `ALIYUN_*` resource
variables listed in `deploy.py`, then run the same command without `--dry-run`.

## Brain Namespaces

| Namespace | Access | Contents |
|---|---|---|
| `shared.code-conventions` | read | Language and style rules shared across agents |
| `git-committer.private` | read/write | Per-repo commit history and learned preferences |
