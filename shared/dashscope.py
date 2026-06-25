"""Shared Qwen client for all agents.

ponytail: DashScope speaks OpenAI's API, so the "client" is just the openai SDK
pointed at the compatible endpoint — no custom auth/retry/streaming code.
Add the native `dashscope` SDK only when an agent needs audio (qwen2-audio).
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url=os.environ.get(
        "DASHSCOPE_BASE_URL",
        "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    ),
)

CHAT_MODEL = os.environ.get("QWEN_CHAT_MODEL", "qwen-plus")
EMBED_MODEL = os.environ.get("QWEN_EMBED_MODEL", "text-embedding-v3")


def chat(prompt: str, model: str = CHAT_MODEL) -> str:
    """One-shot chat completion. Returns the reply text."""
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def embed(text: str, model: str = EMBED_MODEL) -> list[float]:
    """Embed one string. Returns the vector."""
    resp = client.embeddings.create(model=model, input=text)
    return resp.data[0].embedding
