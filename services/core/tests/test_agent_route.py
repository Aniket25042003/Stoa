"""Tests for agent route classification."""

from unittest.mock import patch

from stoa_core.agent.route import classify_agent_route, requires_tools_route


def test_classify_tools_for_cross_feature_keyword():
    assert classify_agent_route("Where are sales and marketing misaligned?") == "tools"


def test_requires_tools_compare_campaign_competitive():
    assert requires_tools_route("Compare campaign performance vs competitive intel") is True


@patch("stoa_core.agent.route.invoke_json")
def test_classify_rag_only_from_llm(mock_invoke):
    mock_invoke.return_value = ({"route": "rag_only"}, "vertex")
    assert classify_agent_route("Who was our top customer last quarter?") == "rag_only"

