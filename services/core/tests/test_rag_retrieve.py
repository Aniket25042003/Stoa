from unittest.mock import patch

from stoa_core.rag.retrieve import (
    _apply_token_budget,
    _mmr_dedup,
    _to_context_items,
    retrieve_context,
)


def _cand(content: str, score: float = 1.0, tokens: int = 100) -> dict:
    return {
        "chunk_id": "c1",
        "item_id": "i1",
        "content": content,
        "kind": "document",
        "item_title": "Doc",
        "rrf_score": score,
        "token_count": tokens,
    }


def test_apply_token_budget():
    candidates = [
        _cand("a" * 400, tokens=100),
        _cand("b" * 400, tokens=100),
        _cand("c" * 400, tokens=100),
    ]
    trimmed = _apply_token_budget(candidates, token_budget=250)
    assert len(trimmed) == 2
    assert sum(c["token_count"] for c in trimmed) <= 250


def test_mmr_dedup_reduces_similar():
    candidates = [
        _cand("pain point pricing too high for SMB teams", score=1.0),
        _cand("pain point pricing too high for small business teams", score=0.9),
        _cand("buying trigger security compliance requirements", score=0.8),
    ]
    out = _mmr_dedup(candidates, max_items=2)
    assert len(out) == 2


def test_to_context_items_shape():
    ctx = _to_context_items([_cand("hello world")])
    assert ctx[0]["ref"].startswith("kb:document:")
    assert ctx[0]["text"] == "hello world"


@patch("stoa_core.rag.retrieve.cache_retrieval_result")
@patch("stoa_core.rag.retrieve.cache_query_embedding")
@patch("stoa_core.rag.retrieve.get_cached_retrieval_result", return_value=None)
@patch("stoa_core.rag.retrieve.get_cached_query_embedding", return_value=None)
@patch("stoa_core.rag.retrieve.embed_query", return_value=[0.0] * 3072)
@patch("stoa_core.rag.retrieve._match_knowledge_rpc")
def test_retrieve_context_pipeline(mock_rpc, _eq, _gr, _gc, _cc, _cr):
    mock_rpc.return_value = [_cand("relevant chunk about pain points")]
    with patch("stoa_core.rag.retrieve.rerank_candidates", side_effect=lambda q, c, top_k=None: c):
        result = retrieve_context("org-1", "top pain points", use_cache=False)
    assert len(result) == 1
    assert "pain points" in result[0]["text"]
