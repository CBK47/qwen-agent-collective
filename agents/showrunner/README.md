# showrunner

**Track:** Track 2 - AI Showrunner

## Purpose

Generates scripts, episode outlines, and production briefs by reading shared context (agent events, glossary, cross-agent outputs) and synthesising them into show-ready content.

## Signature Qwen Call

```
Model: qwen-plus (QWEN_CHAT_MODEL)
Input: episode brief + shared agent events + showrunner.private style guide
Output: formatted script or episode outline
```

## Brain Namespaces

| Namespace | Access | Contents |
|---|---|---|
| `shared.*` | read | All shared agent events and facts used as narrative source material |
| `showrunner.private` | read/write | Show bible, episode history, and style guide |
