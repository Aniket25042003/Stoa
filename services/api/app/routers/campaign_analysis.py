"""
File: services/api/app/routers/campaign_analysis.py
Layer: FastAPI Route Layer
Purpose: Campaign analysis API endpoints.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.deps.org_scope import require_onboarded_scope
from app.deps.rate_limit import check_rate_limit
from app.services.audit import write_audit
from app.services.org_context import OrgScope, require_permission
from app.tasks.campaign_analysis import precompute_campaign_analysis
from stoa_core.analytics.aggregate import build_summary_metrics
from stoa_core.analytics.compare import compare_campaigns
from stoa_core.db.supabase import get_supabase_admin

router = APIRouter(prefix="/v1/campaign-analysis", tags=["campaign-analysis"])


@router.get("/summary")
def get_campaign_analysis_summary(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "campaign_analysis:read")
    org_id = scope.org_id
    sb = get_supabase_admin()

    insights_res = (
        sb.table("precomputed_insights")
        .select("key, title, content, citations, created_at")
        .eq("org_id", org_id)
        .eq("scope", "campaign_analysis")
        .order("created_at", desc=True)
        .execute()
    )
    metrics = build_summary_metrics(org_id)

    conn_res = (
        sb.table("integration_connections")
        .select("provider, status")
        .eq("org_id", org_id)
        .in_("provider", ["ga4", "posthog"])
        .eq("status", "active")
        .execute()
    )
    connected = [c["provider"] for c in (conn_res.data or [])]

    return {
        "metrics": metrics,
        "insights": insights_res.data or [],
        "connected_analytics": connected,
        "has_analytics_connection": bool(connected),
    }


@router.get("/metrics")
def get_campaign_metrics(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "campaign_analysis:read")
    return build_summary_metrics(scope.org_id)


@router.get("/compare")
def compare_two_campaigns(
    scope: OrgScope = Depends(require_onboarded_scope),
    a: str = Query(..., min_length=1),
    b: str = Query(..., min_length=1),
) -> dict[str, Any]:
    require_permission(scope, "campaign_analysis:read")
    return compare_campaigns(scope.org_id, a, b)


@router.post("/refresh")
def refresh_campaign_analysis(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "campaign_analysis:refresh")
    check_rate_limit(scope.user_id, limit_per_minute=5, scope="campaign_analysis_refresh")
    precompute_campaign_analysis.delay(scope.org_id, force=True)
    write_audit(
        scope.org_id,
        scope.user_id,
        "refresh",
        "campaign_analysis",
        metadata={"trigger": "manual"},
    )
    return {"status": "queued", "org_id": scope.org_id}
