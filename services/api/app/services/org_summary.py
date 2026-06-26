"""
File: services/api/app/services/org_summary.py
Layer: FastAPI Service Layer
Purpose: Contains reusable backend business logic shared by routes and workers.
Dependencies: Supabase, stoa_core
"""

from __future__ import annotations

from typing import Any

from stoa_core.alignment.aggregate import build_alignment_summary
from stoa_core.alignment.friction import collect_friction_signals
from stoa_core.analytics.aggregate import build_summary_metrics
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.intelligence.structured import aggregate_crm_stats
from stoa_core.org.completeness import compute_completeness


def fetch_org_counts(org_id: str) -> dict[str, int]:
    """Handles fetch org counts logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.

    Returns:
        dict[str, int]: Result produced for the caller.
    """
    sb = get_supabase_admin()
    docs = (
        sb.table("documents").select("id", count="exact").eq("org_id", org_id).execute()
    )
    signals = (
        sb.table("intelligence")
        .select("id", count="exact")
        .eq("org_id", org_id)
        .execute()
    )
    competitors = (
        sb.table("competitors")
        .select("id", count="exact")
        .eq("org_id", org_id)
        .execute()
    )
    alerts = (
        sb.table("competitive_alerts")
        .select("id", count="exact")
        .eq("org_id", org_id)
        .execute()
    )
    campaigns = (
        sb.table("campaigns").select("id", count="exact").eq("org_id", org_id).execute()
    )
    integrations = (
        sb.table("integration_connections")
        .select("id", count="exact")
        .eq("org_id", org_id)
        .eq("status", "active")
        .execute()
    )
    deals = (
        sb.table("canonical_deals")
        .select("id", count="exact")
        .eq("org_id", org_id)
        .execute()
    )
    return {
        "documents": docs.count or 0,
        "signals": signals.count or 0,
        "competitors": competitors.count or 0,
        "alerts": alerts.count or 0,
        "campaigns": campaigns.count or 0,
        "integrations": integrations.count or 0,
        "canonical_deals": deals.count or 0,
    }


def signals_by_kind(org_id: str) -> dict[str, int]:
    """Handles signals by kind logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.

    Returns:
        dict[str, int]: Result produced for the caller.
    """
    sb = get_supabase_admin()
    res = (
        sb.table("intelligence")
        .select("kind")
        .eq("org_id", org_id)
        .limit(500)
        .execute()
    )
    counts: dict[str, int] = {}
    for row in res.data or []:
        kind = row.get("kind") or "unknown"
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def latest_icp_version(org_id: str) -> int | None:
    """Handles latest icp version logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.

    Returns:
        int | None: Result produced for the caller.
    """
    sb = get_supabase_admin()
    res = (
        sb.table("icp_profiles")
        .select("version")
        .eq("org_id", org_id)
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    if not res.data:
        return None
    return res.data[0].get("version")


def build_core_feature_metrics(org_id: str) -> dict[str, Any]:
    """Aggregate dashboard-ready metrics across all six core features."""
    sb = get_supabase_admin()

    crm_stats = aggregate_crm_stats(org_id)
    campaign_analysis = build_summary_metrics(org_id)
    alignment = build_alignment_summary(org_id)
    friction = collect_friction_signals(org_id)

    competitors_res = (
        sb.table("competitors")
        .select("id", count="exact")
        .eq("org_id", org_id)
        .execute()
    )
    alerts_res = (
        sb.table("competitive_alerts")
        .select("severity")
        .eq("org_id", org_id)
        .order("created_at", desc=True)
        .limit(200)
        .execute()
    )
    campaigns_res = (
        sb.table("campaigns")
        .select("id, status, created_at")
        .eq("org_id", org_id)
        .order("created_at", desc=True)
        .limit(200)
        .execute()
    )
    content_res = (
        sb.table("content_assets")
        .select("status, asset_type, generation_metadata")
        .eq("org_id", org_id)
        .order("created_at", desc=True)
        .limit(200)
        .execute()
    )

    alerts = alerts_res.data or []
    campaigns = campaigns_res.data or []
    assets = content_res.data or []

    alert_severity: dict[str, int] = {}
    for row in alerts:
        severity = row.get("severity") or "unknown"
        alert_severity[severity] = alert_severity.get(severity, 0) + 1

    campaign_status: dict[str, int] = {}
    for row in campaigns:
        status = row.get("status") or "unknown"
        campaign_status[status] = campaign_status.get(status, 0) + 1

    asset_status: dict[str, int] = {}
    generation_times: list[float] = []
    for row in assets:
        status = row.get("status") or "unknown"
        asset_status[status] = asset_status.get(status, 0) + 1
        metadata = row.get("generation_metadata") or {}
        if isinstance(metadata, dict):
            val = metadata.get("generation_time_seconds")
            if isinstance(val, (int, float)):
                generation_times.append(float(val))

    avg_generation_time = (
        round(sum(generation_times) / len(generation_times), 2)
        if generation_times
        else None
    )

    top_industry = (crm_stats.get("top_industries") or [{}])[0]
    top_channel = (campaign_analysis.get("channels", {}).get("top_channel") or {}).get(
        "channel"
    )
    top_campaign = (
        campaign_analysis.get("campaigns", {}).get("best_campaign") or {}
    ).get("campaign")
    top_source = (alignment.get("lead_conversion", {}).get("top_source") or {}).get(
        "source"
    )

    return {
        "icp_customer_research": {
            "best_customer_segment": top_industry.get("name"),
            "deals": crm_stats.get("total_deals", 0),
            "win_rate_percent": crm_stats.get("win_rate_percent"),
            "underperforming_loss_reasons": crm_stats.get("top_loss_reasons", []),
        },
        "content_bottleneck": {
            "status_breakdown": asset_status,
            "avg_generation_time_seconds": avg_generation_time,
        },
        "competitive_intelligence": {
            "tracked_competitors": competitors_res.count or 0,
            "recent_alerts": len(alerts),
            "alerts_by_severity": alert_severity,
        },
        "launch_orchestration": {
            "campaign_count": len(campaigns),
            "status_breakdown": campaign_status,
        },
        "campaign_analysis": {
            "top_channel": top_channel,
            "top_campaign": top_campaign,
            "has_data": campaign_analysis.get("has_data", False),
        },
        "sales_marketing_alignment": {
            "top_lead_source": top_source,
            "stall_points": alignment.get("stall_points", {}).get(
                "top_stall_stages", []
            ),
            "top_friction_loss_reasons": friction.get("top_loss_reasons", []),
        },
    }


def build_completeness_for_org(
    org: dict[str, Any],
    *,
    counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Handles build completeness for org logic for the surrounding Stoa workflow.

    Args:
        org (dict[str, Any]): Input value used by this workflow step.
        counts (dict[str, int] | None): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    org_id = org["id"]
    resolved = counts or fetch_org_counts(org_id)
    return compute_completeness(
        org,
        document_count=resolved["documents"],
        competitor_count=resolved["competitors"],
        integration_count=resolved.get("integrations", 0),
        canonical_deal_count=resolved.get("canonical_deals", 0),
    )
