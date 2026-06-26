"""API tests for campaign analysis and alignment routes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_scope():
    scope = MagicMock()
    scope.org_id = "00000000-0000-4000-8000-000000000001"
    scope.user_id = "00000000-0000-4000-8000-000000000002"
    scope.permissions = frozenset(
        {
            "campaign_analysis:read",
            "campaign_analysis:refresh",
            "alignment:read",
            "alignment:refresh",
        }
    )
    return scope


def test_campaign_analysis_summary_requires_auth():
    res = client.get("/v1/campaign-analysis/summary")
    assert res.status_code in (401, 403, 422)


def test_alignment_summary_requires_auth():
    res = client.get("/v1/alignment/summary")
    assert res.status_code in (401, 403, 422)


@patch("app.routers.campaign_analysis.require_onboarded_scope")
@patch("app.routers.campaign_analysis.build_summary_metrics")
@patch("app.routers.campaign_analysis.get_supabase_admin")
def test_campaign_analysis_summary_ok(mock_sb, mock_metrics, mock_dep, mock_scope):
    mock_dep.return_value = mock_scope
    mock_metrics.return_value = {"has_data": True, "channels": {"channels": []}, "campaigns": {"campaigns": []}}
    mock_sb.return_value.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
        data=[]
    )
    mock_sb.return_value.table.return_value.select.return_value.eq.return_value.in_.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[]
    )

    from app.deps.org_scope import require_onboarded_scope

    app.dependency_overrides[require_onboarded_scope] = lambda: mock_scope
    try:
        res = client.get("/v1/campaign-analysis/summary")
        assert res.status_code == 200
        body = res.json()
        assert "metrics" in body
        assert "insights" in body
    finally:
        app.dependency_overrides.clear()
