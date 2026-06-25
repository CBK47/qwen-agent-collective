# open-translate

**Track:** Track 4 - Autopilot

## Purpose

Translates documents and UI strings across multiple languages, using a shared glossary to keep terminology consistent across all agents and outputs.

## Signature Qwen Call

```
Model: qwen-plus (QWEN_CHAT_MODEL)
Input: source text + target language + shared.glossary context
Output: translated text with glossary terms locked
```

## Brain Namespaces

| Namespace | Access | Contents |
|---|---|---|
| `shared.glossary` | read/write | Canonical term translations used by all agents |
| `open-translate.private` | read/write | Per-project translation memory and style preferences |
