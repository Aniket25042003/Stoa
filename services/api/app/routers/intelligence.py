from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.deps.org_scope import require_onboarded_scope
from app.deps.rate_limit import check_rate_limit
from app.services.audit import write_audit
from app.services.document_ingestion import (
    delete_document_for_org,
    get_document_for_org,
    is_pasted_document,
    update_pasted_document_for_org,
)
from app.services.org_context import OrgScope, require_permission
from app.tasks.intelligence import precompute_insights, rebuild_icp_profile
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.security.sanitize import validate_doc_type

router = APIRouter(prefix="/v1/intelligence", tags=["intelligence"])


class DocumentUpdateBody(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    content: str | None = Field(default=None, min_length=1, max_length=10 * 1024 * 1024)
    doc_type: str | None = Field(default=None, pattern="^(call_transcript|review|crm_export|note)$")


def _serialize_document(doc: dict[str, Any]) -> dict[str, Any]:
    pasted = is_pasted_document(doc)
    return {
        "id": doc["id"],
        "title": doc["title"],
        "doc_type": doc["doc_type"],
        "status": doc["status"],
        "content": doc.get("content"),
        "storage_path": doc.get("storage_path"),
        "source": "paste" if pasted else "upload",
        "editable": pasted,
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


@router.get("/signals")
def list_signals(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "intelligence:read")
    sb = get_supabase_admin()
    res = (
        sb.table("intelligence")
        .select("id, org_id, document_id, kind, content, confidence, evidence, created_at")
        .eq("org_id", scope.org_id)
        .order("created_at", desc=True)
        .limit(200)
        .execute()
    )
    return {"signals": res.data or []}


@router.get("/icp")
def get_icp_profile(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "intelligence:read")
    sb = get_supabase_admin()
    res = (
        sb.table("icp_profiles")
        .select("id, org_id, version, profile, signal_count, created_at")
        .eq("org_id", scope.org_id)
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    profile = (res.data or [None])[0]
    return {"profile": profile}


@router.post("/icp/rebuild")
def trigger_icp_rebuild(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, str]:
    require_permission(scope, "intelligence:rebuild")
    check_rate_limit(scope.user_id, limit_per_minute=5, scope="icp_rebuild")
    rebuild_icp_profile.delay(scope.org_id)
    return {"status": "queued"}


@router.get("/insights")
def list_prepared_insights(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "insights:read")
    sb = get_supabase_admin()
    res = (
        sb.table("precomputed_insights")
        .select("id, org_id, scope, key, title, content, citations, is_stale, created_at")
        .eq("org_id", scope.org_id)
        .eq("scope", "intelligence")
        .order("created_at", desc=True)
        .execute()
    )
    return {"insights": res.data or []}


@router.post("/insights/refresh")
def refresh_prepared_insights(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, str]:
    require_permission(scope, "insights:refresh")
    check_rate_limit(scope.user_id, limit_per_minute=5, scope="insights_refresh")
    precompute_insights.delay(scope.org_id, force=True)
    return {"status": "queued"}


@router.get("/documents")
def list_documents(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "documents:read")
    sb = get_supabase_admin()
    res = (
        sb.table("documents")
        .select("id, title, doc_type, created_at, status")
        .eq("org_id", scope.org_id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"documents": res.data or []}


@router.get("/documents/{document_id}")
def get_document(document_id: str, scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "documents:read")
    doc = get_document_for_org(scope.org_id, document_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return {"document": _serialize_document(doc)}


@router.patch("/documents/{document_id}")
def update_document(
    document_id: str,
    body: DocumentUpdateBody,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, Any]:
    require_permission(scope, "documents:write")
    check_rate_limit(scope.user_id, limit_per_minute=30, scope="document_update")
    if body.doc_type is not None:
        validate_doc_type(body.doc_type)
    try:
        updated = update_pasted_document_for_org(
            scope.org_id,
            document_id,
            scope.user_id,
            title=body.title,
            content=body.content,
            doc_type=body.doc_type,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if message == "Document not found" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code, message) from exc

    write_audit(scope.org_id, scope.user_id, "document.updated", "document", document_id)
    return {"document": _serialize_document(updated)}


@router.delete("/documents/{document_id}")
def delete_document(document_id: str, scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, str]:
    require_permission(scope, "documents:delete")
    deleted = delete_document_for_org(scope.org_id, document_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    write_audit(scope.org_id, scope.user_id, "document.deleted", "document", document_id)
    return {"status": "deleted"}
