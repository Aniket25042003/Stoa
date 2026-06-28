"""Tests for org-aware agent route resolver."""

from unittest.mock import patch

from stoa_core.agent.route import requires_tools_route
from stoa_core.agent.route_resolver import (
    jaccard_similarity,
    resolve_agent_route,
)


def test_requires_tools_route_alignment():
    assert requires_tools_route("Where are sales and marketing misaligned?") is True


def test_requires_tools_route_simple_icp_false():
    assert (
        requires_tools_route(
            "Who are our highest-converting customers and what segments should we prioritize?"
        )
        is False
    )


def test_jaccard_similarity_high_for_paraphrase():
    a = "Who are our highest-converting customers?"
    b = "Who are our highest-converting customers and what segments should we prioritize?"
    assert jaccard_similarity(a, b) >= 0.5


@patch("stoa_core.agent.route_resolver.invoke_json")
@patch("stoa_core.agent.route_resolver._load_org_insights")
def test_resolve_precomputed_enriched(mock_load, mock_invoke):
    mock_invoke.return_value = ({"route": "rag_only"}, "vertex")
    mock_load.return_value = [
        {
            "key": "top_converting_customers",
            "title": "Who are our highest-converting customers?",
            "scope": "intelligence",
            "is_stale": False,
            "content": {"answer": "FinTech segment"},
        }
    ]
    decision = resolve_agent_route(
        "org-1",
        "Who are our highest-converting customers and what segments should we prioritize?",
    )
    assert decision.route == "precomputed_enriched"
    assert decision.matched_insight_key == "top_converting_customers"
    assert decision.confidence >= 0.5


@patch("stoa_core.agent.route_resolver._load_org_insights")
def test_resolve_stale_downgrades_to_rag(mock_load):
    mock_load.return_value = [
        {
            "key": "top_converting_customers",
            "title": "Who are our highest-converting customers?",
            "scope": "intelligence",
            "is_stale": True,
            "content": {"answer": "old"},
        }
    ]
    decision = resolve_agent_route(
        "org-1",
        "Who are our highest-converting customers?",
    )
    assert decision.route == "rag_only"
    assert decision.insight_is_stale is True


@patch("stoa_core.agent.route_resolver.invoke_json")
@patch("stoa_core.agent.route_resolver._load_org_insights")
def test_resolve_tools_bounded_hard_signal(mock_load, mock_invoke):
    mock_load.return_value = []
    decision = resolve_agent_route(
        "org-1",
        "Compare campaign performance vs competitive intel across channels",
    )
    assert decision.route == "tools_bounded"
    mock_invoke.assert_not_called()
