"""Tests for live connector search orchestrator."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from stoa_core.integrations.agent_search import run_agent_search
from stoa_core.integrations.base import AgentSearchHit


@patch("stoa_core.integrations.agent_search.get_connection")
@patch("stoa_core.integrations.agent_search.list_connections")
@patch("stoa_core.integrations.agent_search.get_connector")
@patch("stoa_core.integrations.agent_search.decrypt_credentials")
@patch("stoa_core.integrations.agent_search.maybe_refresh_credentials")
@patch("stoa_core.integrations.agent_search.scope_configured", return_value=True)
def test_run_agent_search_returns_hits(
    _scope,
    _refresh,
    _decrypt,
    mock_get_connector,
    mock_list,
    mock_get_conn,
):
    mock_list.return_value = [
        {"id": "c1", "provider": "hubspot", "status": "active"},
    ]
    mock_get_conn.return_value = {
        "id": "c1",
        "provider": "hubspot",
        "credentials_encrypted": "enc",
        "provider_metadata": {"object_types": ["deals"]},
    }
    connector = MagicMock()
    connector.supports_agent_search.return_value = True
    connector.agent_search.return_value = [
        AgentSearchHit(
            id="d1",
            title="Deal A",
            snippet="Amount=100",
            uri="agent_evidence:hubspot:d1",
            provider="hubspot",
            fetched_at="2026-01-01T00:00:00Z",
        )
    ]
    mock_get_connector.return_value = connector

    hits, err = run_agent_search("org", "hubspot", "top deals")
    assert err is None
    assert len(hits) == 1
    assert hits[0].provider == "hubspot"
    connector.agent_search.assert_called_once()


@patch("stoa_core.integrations.agent_search.list_connections", return_value=[])
def test_run_agent_search_no_connection(mock_list):
    hits, err = run_agent_search("org", "hubspot", "deals")
    assert not hits
    assert err is not None
