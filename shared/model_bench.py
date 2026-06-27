"""Free-tier Qwen model bench.

Exercises each task type the project actually uses — chat, coder, vision, audio,
embed — against a roster of task-relevant free-tier models on DashScope's
OpenAI-compatible endpoint, and prints a comparison table (ok/fail, latency,
sample output or error). Use it to pick the best free-tier model per task.

    python -m shared.model_bench            # all task types
    python -m shared.model_bench chat embed # only these
    python -m shared.model_bench --json     # machine-readable

Reads DASHSCOPE_API_KEY / DASHSCOPE_BASE_URL from the environment (.env).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv()

BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
TIMEOUT = float(os.getenv("QWEN_TIMEOUT_SECONDS", "30"))

# DashScope-hosted sample assets (stable) for the multimodal probes.
SAMPLE_IMAGE = "https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg"
SAMPLE_AUDIO = "https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3"

# Task-relevant free-tier model rosters (the models the PLANs name + close siblings).
ROSTERS: dict[str, list[str]] = {
    "chat":   ["qwen-plus", "qwen-turbo", "qwen-max"],
    "coder":  ["qwen3-coder-plus", "qwen2.5-coder-32b-instruct", "qwen-plus"],
    "vision": ["qwen-vl-max", "qwen-vl-plus"],
    "audio":  ["qwen3-omni-flash", "qwen2-audio-instruct"],
    "embed":  ["text-embedding-v3", "text-embedding-v2", "text-embedding-v1"],
}


def _client() -> OpenAI:
    if not API_KEY:
        sys.exit("DASHSCOPE_API_KEY is not set — populate .env first.")
    return OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=TIMEOUT)


def _chat_probe(client: OpenAI, model: str, prompt: str) -> str:
    r = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}], max_tokens=128,
    )
    return (r.choices[0].message.content or "").strip()


def run_probe(client: OpenAI, task: str, model: str) -> dict:
    """Run one (task, model) probe; return {ok, latency_ms, detail|error}."""
    t0 = time.perf_counter()
    try:
        if task == "chat":
            out = _chat_probe(client, model, "In one sentence, what is a vector database?")
            detail = out[:80]
        elif task == "coder":
            out = _chat_probe(
                client, model,
                "Review this Python and reply with one Conventional Commit subject line only:\n"
                "def add(a,b):\n  return a-b",
            )
            detail = out[:80]
        elif task == "embed":
            r = client.embeddings.create(model=model, input="hackathon memory fact")
            detail = f"dim={len(r.data[0].embedding)}"
        elif task == "vision":
            r = client.chat.completions.create(
                model=model, max_tokens=64,
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "What is in this image? One short sentence."},
                    {"type": "image_url", "image_url": {"url": SAMPLE_IMAGE}},
                ]}],
            )
            detail = (r.choices[0].message.content or "").strip()[:80]
        elif task == "audio":
            r = client.chat.completions.create(
                model=model, max_tokens=64,
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "Transcribe or describe this audio briefly."},
                    {"type": "input_audio", "input_audio": {"data": SAMPLE_AUDIO, "format": "mp3"}},
                ]}],
            )
            detail = (r.choices[0].message.content or "").strip()[:80]
        else:
            return {"ok": False, "latency_ms": 0, "error": f"unknown task {task}"}
        ms = int((time.perf_counter() - t0) * 1000)
        return {"ok": True, "latency_ms": ms, "detail": detail or "(empty)"}
    except Exception as exc:  # noqa: BLE001 — a failed model is useful signal, not fatal
        ms = int((time.perf_counter() - t0) * 1000)
        msg = str(exc).splitlines()[0][:90]
        return {"ok": False, "latency_ms": ms, "error": msg}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Free-tier Qwen model bench")
    ap.add_argument("tasks", nargs="*", choices=list(ROSTERS) + [], help="task types to run (default: all)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = ap.parse_args(argv)

    tasks = args.tasks or list(ROSTERS)
    client = _client()
    rows: list[dict] = []
    for task in tasks:
        for model in ROSTERS[task]:
            res = run_probe(client, task, model)
            rows.append({"task": task, "model": model, **res})

    if args.json:
        print(json.dumps(rows, indent=2))
        return 0

    print(f"\nDashScope free-tier model bench  ({BASE_URL})\n")
    print(f"{'TASK':<7} {'MODEL':<30} {'OK':<4} {'ms':>6}  RESULT")
    print("-" * 96)
    for r in rows:
        ok = "✓" if r["ok"] else "✗"
        result = r.get("detail") if r["ok"] else f"ERR: {r.get('error')}"
        print(f"{r['task']:<7} {r['model']:<30} {ok:<4} {r['latency_ms']:>6}  {result}")
    ok_n = sum(1 for r in rows if r["ok"])
    print(f"\n{ok_n}/{len(rows)} probes succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
