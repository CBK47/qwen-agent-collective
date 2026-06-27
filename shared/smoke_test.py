"""Spine smoke test: prove a real Qwen chat + embedding call works.

Run once the DASHSCOPE_API_KEY is set:
    pip install -r requirements.txt
    python shared/smoke_test.py
"""

try:
    from shared.dashscope import chat, embed
    from shared.brain import ingest_manifest, retrieve_manifest
except ModuleNotFoundError:  # supports `python shared/smoke_test.py`
    from dashscope import chat, embed
    from brain import ingest_manifest, retrieve_manifest


def main() -> None:
    reply = chat("Reply with the single word: pong")
    assert reply and reply.strip(), "chat returned empty"
    print(f"chat  -> {reply.strip()!r}")

    vec = embed("hello brain")
    assert len(vec) > 0, "embedding returned empty vector"
    print(f"embed -> dim {len(vec)}")

    # Test manifest ingestion and retrieval
    manifest_data = {"id": "test_manifest", "content": "Test manifest data"}
    ingest_manifest(manifest_data)
    retrieved = retrieve_manifest("test_manifest")
    assert retrieved == manifest_data, "Retrieved manifest does not match ingested data"
    print("manifest -> ingest/retrieve OK")

    print("OK: spine proven.")


if __name__ == "__main__":
    main()
