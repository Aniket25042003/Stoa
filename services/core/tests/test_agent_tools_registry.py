"""Tests for agent tool registry composition."""

from __future__ import annotations

from unittest.mock import patch

from stoa_core.agent.tools.registry import AGENT_MEMORY_KINDS, build_agent_tools


def test_agent_memory_kinds_includes_search_evidence():
    assert "agent_search_evidence" in AGENT_MEMORY_KINDS


@patch("stoa_core.agent.tools.web.get_settings")
@patch("stoa_core.agent.tools.memory.get_supabase_admin")
def test_build_agent_tools_includes_tiers(mock_sb, mock_settings):
    mock_settings.return_value.disable_external_research = True
    chain = mock_sb.return_value.table.return_value.select.return_value.eq.return_value
    chain.execute.return_value.data = []
    tools = build_agent_tools("org-1", "conv-1", include_web=True)
    names = {t.name for t in tools}
    assert "search_workspace_memory" in names
    assert "get_workspace_freshness" in names
    assert "search_connected_sources" in names
    assert "refresh_connected_source" in names
    assert "lookup_canonical_records" in names
    assert "icp_customer_research_tool" in names
    assert "search_public_web" in names
    assert len(tools) >= 14
