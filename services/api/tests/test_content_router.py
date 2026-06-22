"""
File: services/api/tests/test_content_router.py
Layer: Test Suite
Purpose: Covers unit tests for the content generation FastAPI router.
Dependencies: fastapi, pytest, unittest.mock, Supabase
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.org_context import OrgScope
from app.deps.org_scope import require_onboarded_scope
from app.deps.rate_limit import check_rate_limit

client = TestClient(app)


def mock_scope() -> OrgScope:
    return OrgScope(
        user_id="user-123",
        org_id="org-1",
        membership={"organizations": {"onboarding_completed_at": "2026-06-21T00:00:00Z"}},
        role_key="analyst",
        role_name="Analyst",
        permissions=frozenset({"content:read", "content:create", "content:write", "content:delete"}),
        is_owner=False
    )


@pytest.fixture
def mock_auth():
    app.dependency_overrides[require_onboarded_scope] = mock_scope
    app.dependency_overrides[check_rate_limit] = lambda *args, **kwargs: None
    yield
    app.dependency_overrides.clear()


def test_list_content_assets(mock_auth) -> None:
    mock_assets = [
        {
            "id": "asset-1",
            "org_id": "org-1",
            "asset_type": "image",
            "prompt": "Test prompt",
            "files": [{"storage_path": "org-1/asset-1/0.png", "mime_type": "image/png"}],
            "status": "completed",
            "config": {"aspect_ratio": "1:1"}
        }
    ]
    
    sb_mock = MagicMock()
    sb_mock.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(data=mock_assets)
    # Mock create_signed_url
    signed_url_mock = MagicMock()
    signed_url_mock.signedURL = "http://signed-url/image.png"
    sb_mock.storage.from_.return_value.create_signed_url.return_value = signed_url_mock
    
    with patch("app.routers.content.get_supabase_admin", return_value=sb_mock):
        response = client.get("/v1/content")
        assert response.status_code == 200
        data = response.json()
        assert "assets" in data
        assert len(data["assets"]) == 1
        assert data["assets"][0]["files"][0]["public_url"] == "http://signed-url/image.png"
        sb_mock.storage.from_.assert_called_with("content-assets")


def test_create_content_generation(mock_auth) -> None:
    mock_inserted = {
        "id": "asset-new",
        "org_id": "org-1",
        "asset_type": "image",
        "prompt": "Cool visual of sunset",
        "status": "queued",
        "config": {"aspect_ratio": "16:9", "number_of_images": 1}
    }
    
    sb_mock = MagicMock()
    sb_mock.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[mock_inserted])
    
    with patch("app.routers.content.get_supabase_admin", return_value=sb_mock), \
         patch("app.routers.content.generate_content_asset") as mock_task, \
         patch("app.routers.content.write_audit") as mock_audit:
         
        payload = {
            "prompt": "Cool visual of sunset",
            "asset_type": "image",
            "config": {
                "aspect_ratio": "16:9",
                "number_of_images": 1
            }
        }
        
        response = client.post("/v1/content", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["asset"]["id"] == "asset-new"
        assert data["asset"]["status"] == "queued"
        
        mock_task.delay.assert_called_once_with("asset-new")
        mock_audit.assert_called_once_with("org-1", "user-123", "content.queued", "content_asset", "asset-new")


def test_delete_content_asset(mock_auth) -> None:
    mock_asset = {
        "files": [{"storage_path": "org-1/asset-delete/0.png"}]
    }
    
    sb_mock = MagicMock()
    # Mock retrieve
    sb_mock.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[mock_asset])
    # Mock delete executions
    sb_mock.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock()
    
    with patch("app.routers.content.get_supabase_admin", return_value=sb_mock), \
         patch("app.routers.content.write_audit") as mock_audit:
         
        response = client.delete("/v1/content/asset-delete")
        assert response.status_code == 200
        assert response.json() == {"status": "deleted"}
        
        # Verify removal of files from storage
        sb_mock.storage.from_.return_value.remove.assert_called_once_with(["org-1/asset-delete/0.png"])
        mock_audit.assert_called_once_with("org-1", "user-123", "content.deleted", "content_asset", "asset-delete")
