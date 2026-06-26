#!/usr/bin/env python3
"""memory-echo session logger.

Claude Code SessionEnd hook: reads the session transcript, has qwen-plus write a
TLDR, and appends a dated entry to session-log.md. This file IS memory-echo's
memory until the real agent + Qdrant exist; ingest it then.

Hook mode:  receives the SessionEnd JSON on stdin (has `transcript_path`).
Self-check: `python3 session_logger.py --check` (offline, no API call).

ponytail: reuses shared.dashscope (auth/endpoint/model) instead of a new client.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # repo root
LOG = Path(__file__).resolve().parent / "session-log.md"

SYSTEM = (
    "You are memory-echo, the MemoryAgent for the qwen-agent-collective. "
    "Summarize this Claude Code session into a terse TLDR log entry: 2-5 bullet "
    "points of what was actually DONE or DECIDED. Invent nothing that isn't in "
    "the transcript; if it was a thin session, write fewer bullets. Output only "
    "the bullet lines, each starting with '- '. No preamble, no headers."
)


def extract(transcript_path: str) -> str:
    """Flatten a transcript .jsonl into 'role: text' lines (tool noise dropped)."""
    out = []
    for raw in Path(transcript_path).read_text(errors="replace").splitlines():
        try:
            obj = json.loads(raw)
        except ValueError:
            continue
        if obj.get("type") not in ("user", "assistant"):
            continue
        msg = obj.get("message", {})
        role = msg.get("role", obj["type"])
        content = msg.get("content")
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            parts = []
            for b in content:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    parts.append(b.get("text", ""))
                elif b.get("type") == "tool_use":
                    parts.append(f"[tool:{b.get('name')}]")
            text = "\n".join(p for p in parts if p)
        else:
            text = ""
        text = text.strip()
        if text:
            out.append(f"{role}: {text}")
    return "\n".join(out)


def summarize(convo: str) -> str:
    """qwen-plus TLDR. ponytail: 30s timeout so a stuck call can't hang exit."""
    from shared.dashscope import client, CHAT_MODEL  # imported late: needs DASHSCOPE_API_KEY
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": convo[-30000:]},  # last ~30k chars is plenty
        ],
        timeout=30,
    )
    return resp.choices[0].message.content.strip()


def append_entry(session_id: str, bullets: str) -> None:
    if not LOG.exists():
        LOG.write_text("# memory-echo · session log\n\nAppend-only TLDRs of Claude Code sessions, written by qwen-plus.\n")
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = f"\n## {stamp} · {session_id[:8] or 'unknown'}\n"
    LOG.write_text(LOG.read_text() + header + bullets.rstrip() + "\n")


def main() -> int:
    if "--check" in sys.argv:
        return _self_check()
    try:
        data = json.load(sys.stdin)
    except (ValueError, json.JSONDecodeError):
        return 0  # not invoked as a hook; nothing to do
    path = data.get("transcript_path")
    if not path or not Path(path).exists():
        return 0
    sys.path.insert(0, str(ROOT))
    try:
        convo = extract(path)
        if not convo.strip():
            return 0
        bullets = summarize(convo)
        if bullets:
            append_entry(data.get("session_id", ""), bullets)
    except Exception as e:  # ponytail: a hook must never block session exit
        sys.stderr.write(f"[memory-echo logger] skipped: {e}\n")
    return 0


def _self_check() -> int:
    """Offline: synthetic transcript -> extract + format, assert it holds. No API."""
    import tempfile
    fake = [
        {"type": "user", "message": {"role": "user", "content": "fix the bug"}},
        {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "text", "text": "Found it in foo.py"},
            {"type": "tool_use", "name": "Edit"},
        ]}},
        {"type": "summary", "summary": "ignore me"},
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
        f.write("\n".join(json.dumps(o) for o in fake))
        tp = f.name
    convo = extract(tp)
    assert "user: fix the bug" in convo, convo
    assert "assistant: Found it in foo.py" in convo, convo
    assert "[tool:Edit]" in convo, convo
    assert "ignore me" not in convo, "should skip non-user/assistant lines"
    # format check with a stub summary (no API)
    global LOG
    LOG = Path(tempfile.mkdtemp()) / "session-log.md"
    append_entry("abcd1234ef", "- did a thing\n- decided another")
    body = LOG.read_text()
    assert "## " in body and "abcd1234" in body and "- did a thing" in body, body
    print("self-check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
