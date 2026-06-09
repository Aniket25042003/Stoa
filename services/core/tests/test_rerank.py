from unittest.mock import patch

from stoa_core.rag.rerank import _bm25_rerank, rerank_candidates


def test_bm25_prefers_keyword_match():
    candidates = [
        {"content": "unrelated general marketing advice", "rrf_score": 0.9},
        {"content": "pricing objections from SMB sales teams", "rrf_score": 0.5},
        {"content": "company culture and hiring notes", "rrf_score": 0.4},
    ]
    out = _bm25_rerank("pricing objections SMB", candidates, top_k=2)
    assert out[0]["content"].startswith("pricing objections")
    assert out[0]["rerank_method"] == "bm25"


@patch("stoa_core.rag.rerank._vertex_batch_llm_rerank", return_value=None)
@patch("stoa_core.rag.rerank._cohere_rerank", return_value=None)
def test_rerank_cascade_falls_to_bm25(mock_cohere, mock_vertex):
    candidates = [
        {"content": "noise and filler text", "rrf_score": 0.9},
        {"content": "customer pain point: integration complexity", "rrf_score": 0.5},
    ]
    out = rerank_candidates("integration pain point", candidates, top_k=1)
    assert len(out) == 1
    assert out[0]["rerank_method"] == "bm25"
    assert "integration" in out[0]["content"]
    mock_cohere.assert_called_once()
    mock_vertex.assert_called_once()


@patch("stoa_core.rag.rerank._cohere_rerank")
def test_rerank_uses_cohere_when_available(mock_cohere):
    mock_cohere.return_value = [{"content": "best", "rerank_score": 0.99, "rerank_method": "cohere"}]
    out = rerank_candidates("query", [{"content": "best"}], top_k=1)
    assert out[0]["rerank_method"] == "cohere"
    mock_cohere.assert_called_once()
