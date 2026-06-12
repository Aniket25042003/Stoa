from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.deps.org_scope import require_onboarded_scope
from app.deps.rate_limit import check_rate_limit
from app.services.org_context import OrgScope, require_permission
from app.tasks.intelligence import precompute_insights, rebuild_icp_profile
from stoa_core.db.supabase import get_supabase_admin

router = APIRouter(prefix="/v1/intelligence", tags=["intelligence"])


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
