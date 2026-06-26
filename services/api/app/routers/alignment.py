"""
File: services/api/app/routers/alignment.py
Layer: FastAPI Route Layer
Purpose: Sales–marketing alignment API endpoints.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.deps.org_scope import require_onboarded_scope
from app.deps.rate_limit import check_rate_limit
from app.services.audit import write_audit
from app.services.org_summary import latest_icp_version
from app.services.org_context import OrgScope, require_permission
from app.tasks.alignment import precompute_alignment
from stoa_core.alignment.aggregate import build_alignment_summary
from stoa_core.alignment.friction import collect_friction_signals
from stoa_core.db.supabase import get_supabase_admin

router = APIRouter(prefix="/v1/alignment", tags=["alignment"])


@router.get("/summary")
def get_alignment_summary(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "alignment:read")
    org_id = scope.org_id
    sb = get_supabase_admin()

    insights_res = (
        sb.table("precomputed_insights")
        .select("key, title, content, citations, created_at")
        .eq("org_id", org_id)
        .eq("scope", "alignment")
        .order("created_at", desc=True)
        .execute()
    )
    summary = build_alignment_summary(org_id)
    friction = collect_friction_signals(org_id)

    conn_res = (
        sb.table("integration_connections")
        .select("provider, status")
        .eq("org_id", org_id)
        .in_("provider", ["hubspot", "salesforce"])
        .eq("status", "active")
        .execute()
    )
    connected = [c["provider"] for c in (conn_res.data or [])]

    return {
        "alignment": summary,
        "friction": friction,
        "insights": insights_res.data or [],
        "icp_version": latest_icp_version(org_id),
        "connected_crm": connected,
        "has_crm_connection": bool(connected),
    }


@router.get("/pipeline")
def get_alignment_pipeline(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "alignment:read")
    summary = build_alignment_summary(scope.org_id)
    return {
        "lead_conversion": summary.get("lead_conversion"),
        "campaign_revenue": summary.get("campaign_revenue"),
        "stall_points": summary.get("stall_points"),
    }


@router.get("/friction")
def get_alignment_friction(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "alignment:read")
    return collect_friction_signals(scope.org_id)


@router.post("/refresh")
def refresh_alignment(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "alignment:refresh")
    check_rate_limit(scope.user_id, limit_per_minute=5, scope="alignment_refresh")
    precompute_alignment.delay(scope.org_id, force=True)
    write_audit(
        scope.org_id,
        scope.user_id,
        "refresh",
        "alignment",
        metadata={"trigger": "manual"},
    )
    return {"status": "queued", "org_id": scope.org_id}
