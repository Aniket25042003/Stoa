from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.deps.auth import verify_supabase_jwt
from app.main import app

client = TestClient(app)


def _override_auth():
    app.dependency_overrides[verify_supabase_jwt] = lambda: "user-1"


def test_dashboard_summary_shape():
    _override_auth()
    membership = {
        "org_id": "org-1",
        "organizations": {
            "id": "org-1",
            "name": "Acme",
            "industry": "SaaS",
            "profile": {"brand_voice": "Direct"},
        },
    }
    counts = {"documents": 2, "signals": 5, "competitors": 1, "alerts": 0, "campaigns": 0}
    with (
        patch("app.routers.dashboard.get_user_membership", return_value=membership),
        patch("app.routers.dashboard.fetch_org_counts", return_value=counts),
        patch("app.routers.dashboard.build_completeness_for_org") as mock_completeness,
        patch("app.routers.dashboard.signals_by_kind", return_value={"pain_point": 3}),
        patch("app.routers.dashboard.latest_icp_version", return_value=1),
        patch("app.routers.dashboard.get_supabase_admin") as mock_sb,
    ):
        mock_completeness.return_value = {
            "score": 60,
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
    app.dependency_overrides.clear()
