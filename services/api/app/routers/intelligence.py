from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.deps.auth import verify_supabase_jwt
from app.deps.rate_limit import check_rate_limit
from app.services.org_context import get_user_membership, require_role
from app.tasks.intelligence import precompute_insights, rebuild_icp_profile
from stoa_core.db.supabase import get_supabase_admin

router = APIRouter(prefix="/v1/intelligence", tags=["intelligence"])


@router.get("/signals")
def list_signals(user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    sb = get_supabase_admin()
    res = (
        sb.table("intelligence")
        .select("id, org_id, document_id, kind, content, confidence, evidence, created_at")
        .eq("org_id", membership["org_id"])
        .order("created_at", desc=True)
        .limit(200)
        .execute()
    )
    return {"signals": res.data or []}


@router.get("/icp")
def get_icp_profile(user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    sb = get_supabase_admin()
    res = (
        sb.table("icp_profiles")
        .select("id, org_id, version, profile, signal_count, created_at")
        .eq("org_id", membership["org_id"])
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    profile = (res.data or [None])[0]
    return {"profile": profile}


@router.post("/icp/rebuild")
def trigger_icp_rebuild(user_id: str = Depends(verify_supabase_jwt)) -> dict[str, str]:
    membership = get_user_membership(user_id)
    require_role(membership, "analyst")
    check_rate_limit(user_id, limit_per_minute=5, scope="icp_rebuild")
    rebuild_icp_profile.delay(membership["org_id"])
    return {"status": "queued"}


@router.get("/insights")
def list_prepared_insights(user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    sb = get_supabase_admin()
    res = (
        sb.table("precomputed_insights")
        .select("id, org_id, scope, key, title, content, citations, is_stale, created_at, updated_at")
        .eq("org_id", membership["org_id"])
        .eq("scope", "intelligence")
        .order("created_at", desc=True)
        .execute()
    )
    return {"insights": res.data or []}


@router.post("/insights/refresh")
def refresh_prepared_insights(user_id: str = Depends(verify_supabase_jwt)) -> dict[str, str]:
    membership = get_user_membership(user_id)
    require_role(membership, "analyst")
    check_rate_limit(user_id, limit_per_minute=5, scope="insights_refresh")
    precompute_insights.delay(membership["org_id"], force=True)
    return {"status": "queued"}


@router.get("/documents")
def list_documents(user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    sb = get_supabase_admin()
    res = (
        sb.table("documents")
        .select("id, title, doc_type, created_at, status")
        .eq("org_id", membership["org_id"])
        .order("created_at", desc=True)
        .execute()
    )
    return {"documents": res.data or []}
