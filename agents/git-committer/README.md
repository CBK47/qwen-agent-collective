# git-committer

**Track:** Track 3 - Agent Society

## Purpose

Reviews staged diffs and writes conventional commit messages, following shared code conventions from the brain. Demonstrates an agent that both reads shared context and contributes back to it.

## Setup

To use the git-committer agent with DashScope, follow these steps:

1. **Obtain API Key**: Log in to the [DashScope console](https://dashscope.console.aliyun.com/) and navigate to the API Key section to generate or retrieve your API key.

2. **Create .env File**: In the root directory of the project, create a `.env` file if it doesn't already exist.

3. **Set API Key**: Add the following line to the `.env` file, replacing `your_api_key_here` with your actual DashScope API key:
   ```
   DASHSCOPE_API_KEY=your_api_key_here
   ```

## Signature Qwen Call

```
Model: qwen2.5-coder-32b-instruct (QWEN_CODER_MODEL)
Input: git diff + shared.code-conventions context
Output: conventional commit message + optional inline review notes
```

## Brain Namespaces

| Namespace | Access | Contents |
|---|---|---|
| `shared.code-conventions` | read | Language and style rules shared across agents |
| `git-committer.private` | read/write | Per-repo commit history and learned preferences |
