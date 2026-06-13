from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.deps.org_scope import require_onboarded_scope
from app.main import app
from app.services.org_context import OrgScope

client = TestClient(app)


def _mock_scope() -> OrgScope:
    return OrgScope(
        user_id="user-1",
        org_id="org-1",
        membership={
            "id": "mem-1",
            "org_id": "org-1",
            "role": "owner",
            "organizations": {
                "id": "org-1",
                "name": "Acme",
                "industry": "SaaS",
                "profile": {"brand_voice": "Direct"},
            },
            "org_roles": {"role_key": "owner", "name": "Owner", "permissions": []},
        },
        role_key="owner",
        role_name="Owner",
        permissions=frozenset({"intelligence:read", "documents:read"}),
        is_owner=True,
    )


def test_dashboard_summary_shape():
    app.dependency_overrides[require_onboarded_scope] = _mock_scope
    counts = {
        "documents": 2,
        "signals": 5,
        "competitors": 1,
        "alerts": 0,
        "campaigns": 0,
        "integrations": 0,
        "canonical_deals": 0,
    }
    with (
        patch("app.routers.dashboard.fetch_org_counts", return_value=counts),
        patch("app.routers.dashboard.build_completeness_for_org") as mock_completeness,
        patch("app.routers.dashboard.signals_by_kind", return_value={"pain_point": 3}),
        patch("app.routers.dashboard.latest_icp_version", return_value=1),
        patch("app.routers.dashboard.aggregate_crm_stats", return_value={"total_deals": 0}),
        patch("app.routers.dashboard.get_supabase_admin") as mock_sb,
    ):
        mock_completeness.return_value = {
            "percent": 60,
            "has_documents": True,
            "has_competitors": True,
            "has_brand_voice": True,
            "missing": [],
        }
        sb = MagicMock()
        mock_sb.return_value = sb
        sb.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        sb.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[])

        res = client.get("/v1/dashboard/summary")
        assert res.status_code == 200
        body = res.json()
        assert "counts" in body
        assert "completeness" in body
        assert body["counts"]["documents"] == 2
        assert "crm_stats" in body
    app.dependency_overrides.clear()
