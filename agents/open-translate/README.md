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

3. Set your API key environment variable. For example:

   ```
   export QWEN_API_KEY='your-api-key-here'
   ```

   (On Windows, use `set QWEN_API_KEY='your-api-key-here'`)

4. Start the WebUI server:
   ```
   python webui.py
   ```

   The console will output the server address (e.g., `Running on http://localhost:8000`).

5. Open your browser and navigate to the displayed URL.

6. The interface will display a text input field, language selection dropdown, and translation output area. Enter source text, select target language, and click "Translate" to see the result.

## Command-Line Usage

To translate text via the command line:

```
python cli.py --text "Hello world" --target-language "es"
```

This will output the translated text to the console.

## Demo

### CLI Demo

1. Ensure you have the agent set up with the API key (see [WebUI Setup and Usage](#webui-setup-and-usage) for prerequisites).

2. Run the following command to translate "Hello world" to Spanish:

   ```
   python cli.py --text "Hello world" --target-language "es"
   ```

3. The expected output is:

   ```
   Hola mundo
   ```

### WebUI Demo

1. Start the WebUI server as described in [WebUI Setup and Usage](#webui-setup-and-usage).

2. Open the WebUI in your browser at `http://localhost:8000`.

3. Enter "Hello world" in the text input field.

4. Select "Spanish" from the language dropdown.

5. Click "Translate".

6. The translated text "Hola mundo" will appear in the output area.

## Alibaba Cloud Deployment

To deploy the open-translate agent on Alibaba Cloud:

1. Log in to the [Alibaba Cloud Console](https://account.alibabacloud.com).

2. Create an ECS instance with a suitable configuration (e.g., Ubuntu 20.04 or later). Ensure the security group allows inbound traffic on port 8000 (or the port used by the WebUI).

3. Connect to your ECS instance via SSH (replace 'ubuntu' with the appropriate username if needed):
   ```
   ssh -i your-key.pem ubuntu@your-instance-ip
   ```

4. Install Python and pip (if not already installed):
   ```
   sudo apt update
   sudo apt install python3 python3-pip -y
   ```

5. Clone the repository:
   ```
   git clone https://github.com/your-repo/open-translate.git
   cd open-translate
   ```

6. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

7. Set your Alibaba Cloud Qwen API key as an environment variable. You can obtain the API key from the [Model Studio](https://help.aliyun.com/zh/model-studio/developer-reference/quick-start) dashboard:
   ```
   export QWEN_API_KEY='your-alibaba-cloud-api-key'
   ```

   (On Windows, use `set QWEN_API_KEY='your-alibaba-cloud-api-key'`)

8. Start the WebUI server:
   ```
   python webui.py
   ```

9. Access the WebUI via your browser at `http://<your-instance-ip>:8000`.
