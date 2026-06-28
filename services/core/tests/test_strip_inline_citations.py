from stoa_core.security.sanitize import strip_inline_citations


def test_strip_doc_citations() -> None:
    raw = (
        "ScaleMart noted price sensitivity [doc:7b06fef2-a710-4886-aa6f-51f4c1235b2c]. "
        "BrightHR questioned redundancy [doc:7224cad7-4961-406e-a5e5-cf3dd4b0a303]."
    )
    cleaned = strip_inline_citations(raw)
    assert "[doc:" not in cleaned
    assert "ScaleMart noted price sensitivity." in cleaned


def test_strip_kb_citations() -> None:
    raw = "FinTech wins often [kb:document:abc:chunk1] in our data."
    assert "[kb:" not in strip_inline_citations(raw)
