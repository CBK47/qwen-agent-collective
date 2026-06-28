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

## WebUI Setup and Usage

To launch the WebUI interface:

1. Navigate to the project directory:
   ```
   cd agents/open-translate
   ```

2. Install dependencies (if not already installed):
   ```
   pip install -r requirements.txt
   ```

3. Start the WebUI server:
   ```
   python webui.py
   ```

   The console will output the server address (e.g., `Running on http://localhost:8000`).

4. Open your browser and navigate to the displayed URL.

5. The interface will display a text input field, language selection dropdown, and translation output area. Enter source text, select target language, and click "Translate" to see the result.
