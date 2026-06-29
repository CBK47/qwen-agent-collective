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

## Demo

To run the Skippy Concierge demo:

1. Navigate to the project root directory (where the `brain` folder is located).
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute the demo:
   ```bash
   python brain/demo/skippy_demo.py
   ```

Example output:

```text
$ python brain/demo/skippy_demo.py
> Please upload an image or enter a text query:
[User uploads a photo of a smart thermostat]
Agent: Detected device: Nest Thermostat E. Checking manual...
Step 1: Check if the thermostat is powered on. If not, ensure the batteries are installed correctly.
Step 2: If the display is blank, verify the wiring connections to the R and C terminals.
For more details, see section 3.1 of the manual.
```

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
