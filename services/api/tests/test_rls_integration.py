"""
File: services/api/tests/test_rls_integration.py
Layer: Test Suite
Purpose: Covers regression and behavior checks for test rls integration in the test suite.
Dependencies: Supabase
"""


from __future__ import annotations

import uuid

import pytest
from postgrest.exceptions import APIError


pytestmark = pytest.mark.integration


def test_viewer_cannot_insert_documents(rls_test_context):
    ctx = rls_test_context
    doc_id = str(uuid.uuid4())
    with pytest.raises(APIError):
        ctx["client_a"].table("documents").insert(
            {
                "id": doc_id,
                "org_id": ctx["org_a"]["id"],
                "title": "RLS test",
                "doc_type": "note",
                "content": "should be blocked",
            }
        ).execute()


def test_viewer_cannot_read_other_org_documents(rls_test_context):
    ctx = rls_test_context
    doc_id = str(uuid.uuid4())
    ctx["admin"].table("documents").insert(
        {
            "id": doc_id,
            "org_id": ctx["org_b"]["id"],
            "title": "Org B secret",
            "doc_type": "note",
            "content": "private",
            "status": "processed",
        }
    ).execute()

    res = ctx["client_a"].table("documents").select("id").eq("id", doc_id).execute()
    assert not res.data

    ctx["admin"].table("documents").delete().eq("id", doc_id).execute()


def test_viewer_can_read_own_org_documents(rls_test_context):
    ctx = rls_test_context
    doc_id = str(uuid.uuid4())
    ctx["admin"].table("documents").insert(
        {
            "id": doc_id,
            "org_id": ctx["org_a"]["id"],
            "title": "Org A visible",
            "doc_type": "note",
            "content": "allowed read",
            "status": "processed",
        }
    ).execute()

    res = ctx["client_a"].table("documents").select("id, title").eq("id", doc_id).execute()
    assert res.data and res.data[0]["title"] == "Org A visible"

    ctx["admin"].table("documents").delete().eq("id", doc_id).execute()


def test_viewer_cannot_delete_documents(rls_test_context):
    ctx = rls_test_context
    doc_id = str(uuid.uuid4())
    ctx["admin"].table("documents").insert(
        {
            "id": doc_id,
            "org_id": ctx["org_a"]["id"],
            "title": "Protected",
            "doc_type": "note",
            "content": "no delete",
            "status": "processed",
        }
    ).execute()

    ctx["client_a"].table("documents").delete().eq("id", doc_id).execute()
    still = ctx["admin"].table("documents").select("id").eq("id", doc_id).execute()
    assert still.data

    ctx["admin"].table("documents").delete().eq("id", doc_id).execute()


def test_dual_membership_can_read_both_orgs(rls_test_context):
    """User in org A and org B can read documents from both (RLS is membership-based)."""
    ctx = rls_test_context
    ctx["admin"].table("memberships").insert(
        {
            "org_id": ctx["org_b"]["id"],
            "user_id": ctx["user_a"].id,
            "role": "viewer",
            "role_id": ctx["roles_b"]["viewer"],
        }
    ).execute()

    doc_a = str(uuid.uuid4())
    doc_b = str(uuid.uuid4())
    ctx["admin"].table("documents").insert(
        {
            "id": doc_a,
            "org_id": ctx["org_a"]["id"],
            "title": "Org A doc",
            "doc_type": "note",
            "content": "a",
            "status": "processed",
        }
    ).execute()
    ctx["admin"].table("documents").insert(
        {
            "id": doc_b,
            "org_id": ctx["org_b"]["id"],
            "title": "Org B doc",
            "doc_type": "note",
            "content": "b",
            "status": "processed",
        }
    ).execute()

    res_a = ctx["client_a"].table("documents").select("id").eq("id", doc_a).execute()
    res_b = ctx["client_a"].table("documents").select("id").eq("id", doc_b).execute()
    assert res_a.data and res_b.data

    ctx["admin"].table("memberships").delete().eq("user_id", ctx["user_a"].id).eq("org_id", ctx["org_b"]["id"]).execute()
    ctx["admin"].table("documents").delete().eq("id", doc_a).execute()
    ctx["admin"].table("documents").delete().eq("id", doc_b).execute()


def test_viewer_cannot_read_integration_credentials(rls_test_context):
    """RLS-001: credentials_encrypted is not client-readable."""
    ctx = rls_test_context
    conn_id = str(uuid.uuid4())
    ctx["admin"].table("integration_connections").insert(
        {
            "id": conn_id,
            "org_id": ctx["org_a"]["id"],
            "provider": "hubspot",
            "label": "RLS creds test",
            "credentials_encrypted": "super-secret-token",
            "status": "active",
        }
    ).execute()

    res = (
        ctx["client_a"]
        .table("integration_connections")
        .select("id, provider, label")
        .eq("id", conn_id)
        .execute()
    )
    assert res.data and res.data[0]["provider"] == "hubspot"
    assert "credentials_encrypted" not in res.data[0]

    with pytest.raises(APIError):
        ctx["client_a"].table("integration_connections").select("credentials_encrypted").eq("id", conn_id).execute()

    ctx["admin"].table("integration_connections").delete().eq("id", conn_id).execute()


def test_viewer_cannot_read_other_org_integration_connections(rls_test_context):
    """RLS-002: integration tables use membership-based org scoping."""
    ctx = rls_test_context
    conn_id = str(uuid.uuid4())
    ctx["admin"].table("integration_connections").insert(
        {
            "id": conn_id,
            "org_id": ctx["org_b"]["id"],
            "provider": "salesforce",
            "label": "Org B connection",
            "status": "active",
        }
    ).execute()

    res = ctx["client_a"].table("integration_connections").select("id").eq("id", conn_id).execute()
    assert not res.data

    ctx["admin"].table("integration_connections").delete().eq("id", conn_id).execute()


def test_viewer_can_read_own_org_content_assets(rls_test_context):
    """RLS-003: viewers with content:read can select org content assets."""
    ctx = rls_test_context
    asset_id = str(uuid.uuid4())
    ctx["admin"].table("content_assets").insert(
        {
            "id": asset_id,
            "org_id": ctx["org_a"]["id"],
            "asset_type": "image",
            "prompt": "visible asset",
            "status": "completed",
        }
    ).execute()

    res = ctx["client_a"].table("content_assets").select("id, prompt").eq("id", asset_id).execute()
    assert res.data and res.data[0]["prompt"] == "visible asset"

    ctx["admin"].table("content_assets").delete().eq("id", asset_id).execute()


def test_viewer_cannot_insert_content_assets(rls_test_context):
    """RLS-003: viewers lack content:create."""
    ctx = rls_test_context
    asset_id = str(uuid.uuid4())
    with pytest.raises(APIError):
        ctx["client_a"].table("content_assets").insert(
            {
                "id": asset_id,
                "org_id": ctx["org_a"]["id"],
                "asset_type": "image",
                "prompt": "blocked insert",
                "status": "queued",
            }
        ).execute()


def test_admin_cannot_read_org_invite_token_hash(rls_test_context):
    """RLS-004: token_hash is not client-readable even for team admins."""
    ctx = rls_test_context
    invite_id = str(uuid.uuid4())
    ctx["admin"].table("memberships").update({"role": "admin", "role_id": ctx["roles_a"]["admin"]}).eq(
        "user_id", ctx["user_a"].id
    ).eq("org_id", ctx["org_a"]["id"]).execute()

    ctx["admin"].table("org_invites").insert(
        {
            "id": invite_id,
            "org_id": ctx["org_a"]["id"],
            "email": f"invite-{invite_id[:8]}@example.com",
            "role": "viewer",
            "role_id": ctx["roles_a"]["viewer"],
            "token_hash": "hashed-invite-token-secret",
            "expires_at": "2099-01-01T00:00:00+00:00",
        }
    ).execute()

    res = ctx["client_a"].table("org_invites").select("id, email, role").eq("id", invite_id).execute()
    assert res.data and res.data[0]["email"].startswith("invite-")
    assert "token_hash" not in res.data[0]

    with pytest.raises(APIError):
        ctx["client_a"].table("org_invites").select("token_hash").eq("id", invite_id).execute()

    ctx["admin"].table("org_invites").delete().eq("id", invite_id).execute()
    ctx["admin"].table("memberships").update({"role": "viewer", "role_id": ctx["roles_a"]["viewer"]}).eq(
        "user_id", ctx["user_a"].id
    ).eq("org_id", ctx["org_a"]["id"]).execute()
