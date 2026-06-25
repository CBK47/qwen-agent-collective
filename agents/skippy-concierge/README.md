# skippy-concierge

**Track:** Track 5 - EdgeAgent (multimodal)

## Purpose

Multimodal concierge agent - handles image, audio, and text inputs to answer questions about devices, manuals, and home systems. Runs on-device where possible; falls back to cloud models for heavy tasks.

## Signature Qwen Calls

```
Vision:  qwen-vl-max (QWEN_VL_MODEL)
         Input: device photo or screenshot
         Output: product identification + relevant manual section

Audio:   qwen2-audio-instruct (QWEN_AUDIO_MODEL)
         Input: voice query wav/mp3
         Output: transcription + intent

Text:    qwen-plus (QWEN_CHAT_MODEL)
         Input: identified device + user intent + manual context
         Output: step-by-step answer
```

## Brain Namespaces

| Namespace | Access | Contents |
|---|---|---|
| `skippy.private` | read/write | User device inventory and preferences |
| `devices` | read/write | Shared device database (model IDs, specs) |
| `skippy_device_manuals` | read | Embedded manual chunks for vector lookup |
