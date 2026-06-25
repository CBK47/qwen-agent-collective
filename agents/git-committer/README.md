# git-committer

**Track:** Track 3 - Agent Society

## Purpose

Reviews staged diffs and writes conventional commit messages, following shared code conventions from the brain. Demonstrates an agent that both reads shared context and contributes back to it.

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
