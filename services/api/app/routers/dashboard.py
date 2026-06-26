"""
File: services/api/app/routers/dashboard.py
Layer: FastAPI Route Layer
Purpose: Exposes authenticated REST endpoints and coordinates validation, permissions, and service calls.
Dependencies: FastAPI, Supabase, stoa_core
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.deps.org_scope import require_onboarded_scope
from app.services.org_context import OrgScope, require_permission
from app.services.org_summary import (
    build_completeness_for_org,
    fetch_org_counts,
    latest_icp_version,
    signals_by_kind,
)
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.intelligence.structured import aggregate_crm_stats

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_dashboard_summary(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    """Handles get dashboard summary logic for the surrounding Stoa workflow.

    Args:
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "intelligence:read")
    org = scope.org
    org_id = scope.org_id
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
    crm_stats = aggregate_crm_stats(org_id)
    profile_res = (
        sb.table("user_profiles")
        .select("full_name, job_title")
        .eq("user_id", scope.user_id)
        .limit(1)
        .execute()
    )
    profile = (profile_res.data or [{}])[0]

    return {
        "org": {"id": org_id, "name": org.get("name"), "industry": org.get("industry")},
        "counts": counts,
        "crm_stats": crm_stats,
        "signals_by_kind": signals_by_kind(org_id),
        "icp_version": latest_icp_version(org_id),
        "completeness": completeness,
        "executive_summary": executive,
        "insight_highlights": insights_res.data or [],
        "viewer": {
            "display_name": profile.get("full_name"),
            "job_title": profile.get("job_title"),
            "role_name": scope.role_name,
            "role_key": scope.role_key,
        },
    }
