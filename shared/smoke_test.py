"""Spine smoke test: prove a real Qwen chat + embedding call works.

Run once the DASHSCOPE_API_KEY is set:
    pip install -r requirements.txt
    python shared/smoke_test.py
"""

try:
    from shared.dashscope import chat, embed
except ModuleNotFoundError:  # supports `python shared/smoke_test.py`
    from dashscope import chat, embed


def main() -> None:
    reply = chat("Reply with the single word: pong")
    assert reply and reply.strip(), "chat returned empty"
    print(f"chat  -> {reply.strip()!r}")

    vec = embed("hello brain")
    assert len(vec) > 0, "embedding returned empty vector"
    print(f"embed -> dim {len(vec)}")

    print("OK: spine proven.")


if __name__ == "__main__":
    main()
