"""Capability probe: what does the current (free-tier) key actually grant?

Hits each model the five agents will need, reports PASS/FAIL + latency. Never
gates — it's a diagnostic, run it after any key/region change:
    python shared/probe.py

ponytail: audio (qwen2-audio) needs the native dashscope SDK + an audio file,
so it's reported as DEFERRED rather than built. Add it when skippy needs voice.
"""

import os
import time

try:
    from shared.dashscope import DashScopeClient
except ModuleNotFoundError:  # supports `python shared/probe.py`
    from dashscope import DashScopeClient

CODER_MODEL = os.environ.get("QWEN_CODER_MODEL", "qwen3-coder-plus")
VL_MODEL = os.environ.get("QWEN_VL_MODEL", "qwen-vl-max")
CHAT_MODEL = os.environ.get("QWEN_CHAT_MODEL", "qwen-plus")
EMBED_MODEL = os.environ.get("QWEN_EMBED_MODEL", "text-embedding-v3")
qwen = DashScopeClient()

# DashScope's own documented sample image — stable, proves vision input works.
SAMPLE_IMAGE = "https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg"


def timed(label, fn):
    t = time.time()
    try:
        info = fn()
        print(f"  PASS  {label:22} {time.time()-t:5.2f}s  {info}")
    except Exception as e:
        msg = str(e).split("\n")[0][:90]
        print(f"  FAIL  {label:22} {time.time()-t:5.2f}s  {type(e).__name__}: {msg}")


def list_models():
    ids = qwen.list_models()
    return f"{len(ids)} models, e.g. {', '.join(ids[:4])}"


def chat(model):
    return repr(qwen.chat("Reply with one word: ok", model=model, max_tokens=8).strip()[:30])


def embed():
    vector = qwen.embed("probe", model=EMBED_MODEL)
    return f"dim {len(vector)}"


def vision():
    text = qwen.chat(
        model=VL_MODEL,
        messages=[{"role": "user", "content": [
            {"type": "text", "text": "What animal is in this image? One word."},
            {"type": "image_url", "image_url": {"url": SAMPLE_IMAGE}},
        ]}],
    )
    return repr(text.strip()[:30])


print("Probing free-tier key capabilities:\n")
timed("models.list", list_models)
timed(f"chat ({CHAT_MODEL})", lambda: chat(CHAT_MODEL))
timed(f"coder ({CODER_MODEL})", lambda: chat(CODER_MODEL))
timed(f"embed ({EMBED_MODEL})", embed)
timed(f"vision ({VL_MODEL})", vision)
print(f"  DEFER audio ({os.environ.get('QWEN_AUDIO_MODEL','qwen2-audio-instruct')})"
      "          needs native dashscope SDK — skipped by design")
print("\nDone.")
