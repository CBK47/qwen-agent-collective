# skippy-concierge

**Track:** Track 5 - EdgeAgent (multimodal)

## Purpose

Multimodal concierge agent - handles image, audio, and text inputs to answer questions about devices, manuals, and home systems. Runs on-device where possible; falls back to cloud models for heavy tasks.

## WebUI

The Skippy Concierge WebUI provides a user-friendly interface for interacting with the concierge agent. It allows users to upload images, record audio, and input text queries to receive step-by-step assistance for device troubleshooting and information.

To run the WebUI locally:

1. Navigate to the `webui` directory:
   ```bash
   cd webui
   ```

2. Install dependencies (if not already installed):
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to `http://localhost:3000` to access the WebUI.

The WebUI is used in the demo video to showcase the multimodal capabilities of the agent, demonstrating real-time interaction with device images, voice commands, and text queries to provide contextual assistance.

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
