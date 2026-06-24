"""
File: services/api/tests/test_security_idor.py
Layer: Test Suite
Purpose: Security regression tests for content IDOR checks and HubSpot webhook auth.
"""

from __future__ import annotations

import json
import time
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.deps.org_scope import require_onboarded_scope
from app.deps.rate_limit import check_public_rate_limit, check_rate_limit
from app.main import app
from app.services.org_context import OrgScope
from stoa_core.integrations.hubspot_webhook import (
    compute_hubspot_signature_v3,
    hubspot_portal_matches_metadata,
    verify_hubspot_signature_v3,
)

client = TestClient(app)


def _mock_scope() -> OrgScope:
    return OrgScope(
        user_id="user-123",
        org_id="org-1",
        membership={"organizations": {"onboarding_completed_at": "2026-06-21T00:00:00Z"}},
        role_key="analyst",
        role_name="Analyst",
        permissions=frozenset({"content:read", "content:create", "content:write", "content:delete"}),
        is_owner=False,
    )


@pytest.fixture
def mock_auth():
    app.dependency_overrides[require_onboarded_scope] = _mock_scope
    app.dependency_overrides[check_rate_limit] = lambda *args, **kwargs: None
    app.dependency_overrides[check_public_rate_limit] = lambda *args, **kwargs: None
    yield
    app.dependency_overrides.clear()


def test_hubspot_signature_v3_round_trip() -> None:
    secret = "test-client-secret"
    body = b'[{"portalId":12345,"subscriptionType":"contact.creation"}]'
    timestamp = str(int(time.time()))
    signature = compute_hubspot_signature_v3(
        client_secret=secret,
        method="POST",
        request_uri="/v1/integrations/webhooks/hubspot",
        body=body,
        timestamp=timestamp,
    )
    assert verify_hubspot_signature_v3(
        client_secret=secret,
        method="POST",
        request_uri="/v1/integrations/webhooks/hubspot",
        body=body,
        signature=signature,
        timestamp=timestamp,
    )


def test_hubspot_portal_metadata_match() -> None:
    assert hubspot_portal_matches_metadata("12345", {"hub_id": 12345})
    assert not hubspot_portal_matches_metadata("99999", {"hub_id": 12345})


@patch("app.routers.integrations.check_public_rate_limit")
@patch("app.routers.integrations.sync_integration_source")
@patch("stoa_core.db.supabase.get_supabase_admin")
@patch("app.routers.integrations.get_settings")
def test_hubspot_webhook_rejects_invalid_signature(mock_settings, mock_admin, mock_delay, _mock_rate) -> None:
    settings = MagicMock()
    settings.hubspot_client_secret = "secret"
    settings.is_development = False
    mock_settings.return_value = settings

    response = client.post(
        "/v1/integrations/webhooks/hubspot",
        content=b"[]",
        headers={"X-HubSpot-Signature-v3": "bad", "X-HubSpot-Request-Timestamp": str(int(time.time()))},
    )
    assert response.status_code == 401
    mock_delay.delay.assert_not_called()


@patch("app.routers.integrations.check_public_rate_limit")
@patch("app.routers.integrations.sync_integration_source")
@patch("stoa_core.db.supabase.get_supabase_admin")
@patch("app.routers.integrations.get_settings")
def test_hubspot_webhook_filters_by_portal_id(mock_settings, mock_admin, mock_delay, _mock_rate) -> None:
    secret = "secret"
    settings = MagicMock()
    settings.hubspot_client_secret = secret
    settings.is_development = False
    mock_settings.return_value = settings

    body = json.dumps([{"portalId": 111, "subscriptionType": "contact.creation"}]).encode()
    timestamp = str(int(time.time()))
    signature = compute_hubspot_signature_v3(
        client_secret=secret,
        method="POST",
        request_uri="/v1/integrations/webhooks/hubspot",
        body=body,
        timestamp=timestamp,
    )

    sb = MagicMock()
    mock_admin.return_value = sb
    sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[
            {"id": "conn-a", "org_id": "org-a", "provider_metadata": {"hub_id": 111}},
            {"id": "conn-b", "org_id": "org-b", "provider_metadata": {"hub_id": 222}},
        ]
    )

    response = client.post(
        "/v1/integrations/webhooks/hubspot",
        content=body,
        headers={
            "X-HubSpot-Signature-v3": signature,
            "X-HubSpot-Request-Timestamp": timestamp,
        },
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1
    mock_delay.delay.assert_called_once_with("conn-a", "org-a")


@patch("stoa_core.db.resource_scope.verify_org_resource")
@patch("app.routers.content.generate_content_asset")
@patch("app.routers.content.write_audit")
@patch("app.routers.content.get_supabase_admin")
def test_create_content_rejects_foreign_campaign(
    mock_admin, mock_audit, mock_task, mock_verify, mock_auth
) -> None:
    mock_verify.side_effect = ValueError("campaigns resource not found for organization")

    response = client.post(
        "/v1/content",
        json={
            "prompt": "A product hero shot for launch",
            "asset_type": "image",
            "campaign_id": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 404
    mock_task.delay.assert_not_called()


@patch("stoa_core.db.resource_scope.verify_org_resource")
@patch("app.routers.content.generate_content_asset")
@patch("app.routers.content.write_audit")
@patch("app.routers.content.get_supabase_admin")
def test_create_content_rejects_foreign_reference_asset(
    mock_admin, mock_audit, mock_task, mock_verify, mock_auth
) -> None:
    def _verify(table, resource_id, org_id, **kwargs):
        if table == "content_assets":
            raise ValueError("content_assets resource not found for organization")
        return {"id": resource_id}

    mock_verify.side_effect = _verify

    response = client.post(
        "/v1/content",
        json={
            "prompt": "Animate this product hero shot",
            "asset_type": "video",
            "reference_asset_id": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 404
    mock_task.delay.assert_not_called()


@patch("app.tasks.content.get_supabase_admin")
@patch("app.tasks.content.publish_event")
@patch("app.tasks.content.enrich_content_prompt", return_value=("enriched", []))
@patch("app.tasks.content.verify_content_asset")
def test_content_task_asserts_reference_asset_org(mock_verify, _mock_enrich, _mock_publish, mock_admin) -> None:
    from app.tasks.content import generate_content_asset

    org_id = str(uuid.uuid4())
    asset_id = str(uuid.uuid4())
    ref_id = str(uuid.uuid4())

    def verify_side_effect(aid: str, oid: str | None = None) -> dict:
        if oid:
            raise ValueError(f"Content asset {ref_id} does not belong to org {org_id}")
        return {
            "id": asset_id,
            "org_id": org_id,
            "campaign_id": None,
            "asset_type": "video",
            "prompt": "test",
            "config": {},
            "reference_asset_id": ref_id,
            "files": [{"storage_path": f"{org_id}/{ref_id}/0.png"}],
        }

    mock_verify.side_effect = verify_side_effect
    sb = MagicMock()
    mock_admin.return_value = sb
    sb.storage.from_.return_value.download.return_value = b"img"

    with patch("app.tasks.content.generate_video", return_value=b"video"), patch.object(
        generate_content_asset, "retry", side_effect=RuntimeError("stop")
    ):
        with pytest.raises(RuntimeError, match="stop"):
            generate_content_asset.run(asset_id)

    mock_verify.assert_any_call(ref_id, org_id)
