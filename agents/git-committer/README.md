# git-committer

**Track:** Track 3 - Agent Society

## Purpose

Reviews staged diffs and writes conventional commit messages, following shared code conventions from the brain. Demonstrates an agent that both reads shared context and contributes back to it.

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

## Alibaba Cloud Deployment

To deploy the git-committer agent to Alibaba Cloud infrastructure, follow these steps:

1. **Obtain Alibaba Cloud Credentials**: Log in to the [Alibaba Cloud RAM Console](https://ram.console.aliyun.com) and navigate to the AccessKey section to create an AccessKey ID and Secret. Ensure the account has necessary permissions for deploying resources.

2. **Update .env File**: Add the following lines to your `.env` file in the project root:

   ```
   ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key_id
   ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_access_key_secret
   ```

3. **Run Deployment Script**: Execute the deployment command:

   ```
   python deploy.py --region cn-hangzhou --instance-type ecs.g7.large
   ```

   Replace `cn-hangzhou` with your desired region and `ecs.g7.large` with the appropriate instance type.

4. **Verify Deployment**: After deployment, verify the agent is running by checking the instance status in the Alibaba Cloud Console or using SSH to connect to the instance and check the agent logs.

## Running the Track 3 Demo

The canonical implementation is `review.py`. It runs three role-specific Qwen
reviewers, a Qwen negotiation step, and a single-agent baseline over the same
diff.

```bash
# JSON output for judging
python agents/git-committer/review.py --diff-file sample.patch

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

- `team_issue_count`: total issues found by the specialist reviewers
- `baseline_issue_count`: issues found by one holistic reviewer
- `delta`: `team_issue_count - baseline_issue_count`

This gives the Track 3 submission a measurable comparison between the
multi-agent society and a single-agent baseline.

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
