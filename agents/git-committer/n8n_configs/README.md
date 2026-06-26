# git-committer n8n configs

## Qwen Project Worker, 30 minute loop

Import `qwen_project_worker_30min.json` into n8n.

This workflow is designed for the DGX Spark n8n instance to orchestrate a safe
repo-review loop every 30 minutes:

```text
schedule -> collect repo/test/config context -> ask Qwen -> write Markdown report
```

It does **not** edit files or push code. It writes reports to:

```text
reports/qwen-worker/YYYY-MM-DD/<timestamp>.md
```

## Required DGX environment

Set these environment variables where the n8n process can read them:

```sh
REPO_PATH=/path/on/dgx/qwen-agent-collective
DASHSCOPE_API_KEY=...
DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_CHAT_MODEL=qwen-plus
QWEN_CODER_MODEL=qwen3-coder-plus
```

If your DashScope key is workspace-scoped, use that workspace base URL instead of
the generic intl URL.

## Important: Docker vs host n8n

If n8n runs directly on the DGX host, `REPO_PATH` can point to any local checkout.

If n8n runs in Docker, the Execute Command node runs **inside the container**.
Either:

1. Mount the repo into the container and set `REPO_PATH` to the container path, or
2. Replace the Execute Command nodes with SSH commands that run on the DGX host.

Example Docker volume shape:

```yaml
volumes:
  - /home/connor/Code/qwen-agent-collective:/repo/qwen-agent-collective
environment:
  - REPO_PATH=/repo/qwen-agent-collective
```

## DGX checkout setup

On the DGX host or inside the n8n container, the checkout needs the repo tooling:

```sh
cd "$REPO_PATH"
python -m pip install -r requirements.txt
cd brain/explorer && npm install
cd "$REPO_PATH"
make test
python -m shared.dashscope doctor --no-network
```

## First manual test

Before activating the schedule, run the workflow manually in n8n.

Expected first result:

- `Collect Repo Context` shows `PASS: doctor --no-network`.
- `Collect Repo Context` shows `PASS: make test`.
- `Ask Qwen For Next Work` returns a chat completion.
- `Write Markdown Report` prints the report path.

If `REPO_PATH` is missing or wrong, the workflow intentionally writes a preflight
failure into the Qwen context instead of crashing silently.

## Later phases

Keep this first loop report-only. Later workflows can add:

- branch creation,
- issue/task selection,
- actual coding worker invocation,
- PR creation,
- daily screenshots,
- blog hero images,
- demo video clips.
