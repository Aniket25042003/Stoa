"""Tests for bounded plan-execute-synthesize agent."""

from unittest.mock import MagicMock, patch

from stoa_core.agent.bounded_agent import _should_block_memory_search, run_bounded_agent_turn


def test_block_memory_search_when_context_rich():
    planned = [{"name": "search_workspace_memory", "args": {"query": "x"}}]
    assert _should_block_memory_search("question", 8, planned) is True
    assert _should_block_memory_search("question", 3, planned) is False


@patch("stoa_core.agent.bounded_agent.invoke_text")
@patch("stoa_core.agent.bounded_agent.plan_tools")
@patch("stoa_core.agent.bounded_agent.build_agent_tools")
def test_bounded_agent_executes_plan(mock_tools, mock_plan, mock_invoke):
    tool = MagicMock()
    tool.name = "icp_customer_research_tool"
    tool.invoke.return_value = '{"feature": "icp"}'
    mock_tools.return_value = [tool]
    mock_plan.return_value = {
        "tools": [{"name": "icp_customer_research_tool", "args": {"query": "segments"}}],
        "reason": "ICP question",
    }
    mock_invoke.return_value = ("FinTech is top segment.", "vertex")

    result = run_bounded_agent_turn(
        "org-1",
        "conv-1",
        "Who converts best?",
        [{"ref": "kb:1", "text": "context"}],
    )
    assert result.route == "tools_bounded"
    assert "icp_customer_research_tool" in result.used_tools
    assert "FinTech" in result.answer
