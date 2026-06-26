"""Tests for query preparation and multi-query retrieval merge."""

from unittest.mock import patch

from stoa_core.rag.query_prepare import (
    PreparedQuery,
    _merge_context_items,
    needs_query_rewrite,
    prepare_query,
    retrieve_context_prepared,
)


def test_needs_rewrite_short_query():
    assert needs_query_rewrite("top customer last quarter?", has_history=False) is True


def test_needs_rewrite_pronoun_with_history():
    assert needs_query_rewrite("what about that?", has_history=True) is True
    long_with_pronoun = (
        "Can you elaborate further on that specific pricing concern for our enterprise "
        "customer accounts this quarter?"
    )
    assert needs_query_rewrite(long_with_pronoun, has_history=False) is False
    assert needs_query_rewrite(long_with_pronoun, has_history=True) is True


def test_prepare_query_skips_long_question():
    long_q = (
        "Who was our highest paying enterprise customer in the last fiscal quarter "
        "and what were the primary reasons they expanded their contract?"
    )
    prepared = prepare_query("org-1", long_q, use_cache=False)
    assert prepared.rewrite_used is False
    assert prepared.search_queries == [long_q]


@patch("stoa_core.rag.query_prepare.invoke_json")
def test_prepare_query_rewrite(mock_invoke):
    mock_invoke.return_value = (
        {
            "standalone_question": "Highest paying customer last quarter by deal amount",
            "search_queries": [
                "top deal amount closed won last quarter",
                "highest revenue customer account Q4",
            ],
        },
        "vertex",
    )
    prepared = prepare_query("org-1", "top customer last quarter?", use_cache=False)
    assert prepared.rewrite_used is True
    assert len(prepared.search_queries) == 3


def test_merge_context_items_dedupes_refs():
    batch_a = [{"ref": "kb:document:a:1", "text": "a", "score": 0.9, "token_count": 10}]
    batch_b = [{"ref": "kb:document:a:1", "text": "a", "score": 0.8, "token_count": 10}]
    merged = _merge_context_items([batch_a, batch_b], final_k=5, token_budget=100)
    assert len(merged) == 1


@patch("stoa_core.rag.query_prepare.retrieve_context")
@patch("stoa_core.rag.query_prepare.prepare_query")
def test_retrieve_context_prepared_multi_query(mock_prepare, mock_retrieve):
    mock_prepare.return_value = PreparedQuery(
        original_question="top customer?",
        standalone_question="top customer?",
        search_queries=["query one", "query two"],
        rewrite_used=True,
    )
    mock_retrieve.side_effect = [
        [{"ref": "kb:document:a:1", "text": "deal A", "score": 0.9, "token_count": 10}],
        [{"ref": "kb:document:b:1", "text": "deal B", "score": 0.8, "token_count": 10}],
    ]
    context, prepared = retrieve_context_prepared("org-1", "top customer?", use_cache=False)
    assert prepared.rewrite_used is True
    assert len(context) == 2
    assert mock_retrieve.call_count == 2
