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

## Deployment on Alibaba Cloud

### Prerequisites

- Alibaba Cloud account with **Model Studio** access
- Alibaba Cloud CLI (`aliyun`) configured with your AccessKey
- Python 3.8+ installed

### Step 1: Configure Credentials

Set your Alibaba Cloud credentials as environment variables:

```bash
export ALIBABA_CLOUD_ACCESS_KEY_ID="your_access_key_id"
export ALIBABA_CLOUD_ACCESS_KEY_SECRET="your_access_key_secret"
```

You can generate these credentials in the [Alibaba Cloud RAM console](https://ram.console.aliyun.com/users).

### Step 2: Deploy the Agent

1. Clone the repository:

```bash
git clone https://github.com/your-repo/showrunner.git
cd showrunner
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the agent:

```bash
python showrunner.py
```

### Step 3: Verification

Check the agent logs for successful initialization and test the agent by sending a sample request:

```bash
curl -X POST http://localhost:8000/generate -H "Content-Type: application/json" -d '{"context": "Generate a script for a sci-fi episode"}'
```
