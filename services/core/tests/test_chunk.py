from stoa_core.ingestion.chunk import chunk_text, chunk_text_strings, estimate_tokens


def test_chunk_short_text():
    chunks = chunk_text("hello")
    assert len(chunks) == 1
    assert chunks[0].content == "hello"
    assert chunks[0].token_count >= 1


def test_chunk_long_text():
    text = "word " * 500
    chunks = chunk_text(text, target_tokens=50, max_tokens=60, overlap_tokens=5)
    assert len(chunks) > 1
    assert all(c.token_count <= 200 for c in chunks)


def test_chunk_text_strings_compat():
    result = chunk_text_strings("short text")
    assert result == ["short text"]


def test_estimate_tokens():
    assert estimate_tokens("hello world") >= 2
