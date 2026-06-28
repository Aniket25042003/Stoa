from stoa_core.llm.content import extract_text_content


def test_extract_text_from_vertex_content_blocks() -> None:
    blocks = [
        {
            "type": "text",
            "text": "Based on your data, prioritize FinTech",
            "thought_signature": "CiIBjz1rX7CelYhpoE6L",
        },
        ".\n\n* FinTech Companies: 42% win rate",
    ]
    assert extract_text_content(blocks) == (
        "Based on your data, prioritize FinTech.\n\n* FinTech Companies: 42% win rate"
    )


def test_extract_text_from_stringified_vertex_blocks() -> None:
    raw = (
        "[{'type': 'text', 'text': 'Hello world', 'thought_signature': 'abc123'}, "
        "'.\\n\\nMore detail here']"
    )
    assert extract_text_content(raw) == "Hello world.\n\nMore detail here"


def test_extract_text_plain_string() -> None:
    assert extract_text_content("Simple answer") == "Simple answer"
