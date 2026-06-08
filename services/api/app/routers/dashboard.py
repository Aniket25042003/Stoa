from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.deps.auth import verify_supabase_jwt
from app.services.org_summary import (
    build_completeness_for_org,
    fetch_org_counts,
    latest_icp_version,
    signals_by_kind,
)
from app.services.org_context import get_user_membership
from stoa_core.db.supabase import get_supabase_admin

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_dashboard_summary(user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    org = membership.get("organizations") or {}
    org_id = membership["org_id"]
    counts = fetch_org_counts(org_id)
    completeness = build_completeness_for_org(org, counts=counts)

    sb = get_supabase_admin()
    insights_res = (
        sb.table("precomputed_insights")
        .select("key, title, content, citations, created_at")
        .eq("org_id", org_id)
        .eq("scope", "intelligence")
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )
    exec_res = (
        sb.table("precomputed_insights")
        .select("content, citations, created_at")
        .eq("org_id", org_id)
        .eq("scope", "dashboard")
        .eq("key", "executive_summary")
        .limit(1)
        .execute()
    )
    executive = (exec_res.data or [None])[0]

    return {
        "org": {"id": org_id, "name": org.get("name"), "industry": org.get("industry")},
        "counts": counts,
        "signals_by_kind": signals_by_kind(org_id),
        "icp_version": latest_icp_version(org_id),
        "completeness": completeness,
        "executive_summary": executive,
        "insight_highlights": insights_res.data or [],
    }
