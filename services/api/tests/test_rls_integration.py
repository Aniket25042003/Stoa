"""Live Supabase RLS integration tests.

Run with:
  RUN_INTEGRATION_TESTS=1 pytest tests/test_rls_integration.py -q

Requires SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET.
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
