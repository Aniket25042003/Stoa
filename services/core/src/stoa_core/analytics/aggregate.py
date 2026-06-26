"""
File: services/core/src/stoa_core/analytics/aggregate.py
Layer: Core Analytics
Purpose: SQL-backed aggregations for channel and campaign performance.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from stoa_core.db.supabase import get_supabase_admin


def _parse_metrics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize metric fact rows for aggregation."""
    out: list[dict[str, Any]] = []
    for row in rows:
        metrics = row.get("metrics") or {}
        sessions = float(metrics.get("sessions") or metrics.get("events") or 0)
        conversions = float(metrics.get("conversions") or 0)
        users = float(metrics.get("users") or metrics.get("totalUsers") or 0)
        conv_rate = round(conversions / sessions * 100, 2) if sessions > 0 else None
        out.append(
            {
                "dimension_value": row.get("dimension_value") or "(not set)",
                "dimension_type": row.get("dimension_type"),
                "source": row.get("source"),
                "sessions": sessions,
                "conversions": conversions,
                "users": users,
                "conversion_rate_percent": conv_rate,
            }
        )
    return out


def load_metric_facts(org_id: str, dimension_type: str | None = None) -> list[dict[str, Any]]:
    """Load latest analytics metric facts for an org."""
    sb = get_supabase_admin()
    q = (
        sb.table("analytics_metric_facts")
        .select("*")
        .eq("org_id", org_id)
        .order("period_end", desc=True)
        .limit(500)
    )
    if dimension_type:
        q = q.eq("dimension_type", dimension_type)
    res = q.execute()
    return res.data or []


def aggregate_channel_metrics(org_id: str) -> dict[str, Any]:
    """Aggregate channel-level conversion metrics."""
    rows = load_metric_facts(org_id, dimension_type="channel")
    if not rows:
        rows = [r for r in load_metric_facts(org_id) if r.get("dimension_type") == "channel"]
    parsed = _parse_metrics(rows)
    if not parsed:
        return {"channels": [], "top_channel": None, "total_sessions": 0, "total_conversions": 0}

    by_channel: dict[str, dict[str, float]] = defaultdict(
        lambda: {"sessions": 0, "conversions": 0, "users": 0}
    )
    for item in parsed:
        ch = item["dimension_value"]
        by_channel[ch]["sessions"] += item["sessions"]
        by_channel[ch]["conversions"] += item["conversions"]
        by_channel[ch]["users"] += item["users"]

    channels = []
    for name, vals in sorted(by_channel.items(), key=lambda x: x[1]["conversions"], reverse=True):
        sessions = vals["sessions"]
        conversions = vals["conversions"]
        channels.append(
            {
                "channel": name,
                "sessions": int(sessions),
                "conversions": int(conversions),
                "users": int(vals["users"]),
                "conversion_rate_percent": (
                    round(conversions / sessions * 100, 2) if sessions > 0 else None
                ),
            }
        )

    top = channels[0] if channels else None
    total_sessions = sum(c["sessions"] for c in channels)
    total_conversions = sum(c["conversions"] for c in channels)
    return {
        "channels": channels,
        "top_channel": top,
        "total_sessions": total_sessions,
        "total_conversions": total_conversions,
    }


def aggregate_campaign_metrics(org_id: str) -> dict[str, Any]:
    """Aggregate campaign-level metrics (GA4 campaign or UTM campaign)."""
    campaign_rows = load_metric_facts(org_id, dimension_type="campaign")
    utm_rows = load_metric_facts(org_id, dimension_type="utm_campaign")
    rows = campaign_rows + utm_rows
    parsed = _parse_metrics(rows)
    if not parsed:
        return {"campaigns": [], "best_campaign": None, "worst_campaign": None}

    by_campaign: dict[str, dict[str, float]] = defaultdict(
        lambda: {"sessions": 0, "conversions": 0}
    )
    for item in parsed:
        name = item["dimension_value"]
        by_campaign[name]["sessions"] += item["sessions"]
        by_campaign[name]["conversions"] += item["conversions"]

    campaigns = []
    for name, vals in by_campaign.items():
        sessions = vals["sessions"]
        conversions = vals["conversions"]
        campaigns.append(
            {
                "campaign": name,
                "sessions": int(sessions),
                "conversions": int(conversions),
                "conversion_rate_percent": (
                    round(conversions / sessions * 100, 2) if sessions > 0 else None
                ),
            }
        )

    campaigns.sort(key=lambda c: c["conversions"], reverse=True)
    best = campaigns[0] if campaigns else None
    worst = campaigns[-1] if len(campaigns) > 1 else None
    return {"campaigns": campaigns, "best_campaign": best, "worst_campaign": worst}


def build_summary_metrics(org_id: str) -> dict[str, Any]:
    """Headline metrics for campaign analysis dashboard."""
    channels = aggregate_channel_metrics(org_id)
    campaigns = aggregate_campaign_metrics(org_id)
    return {
        "channels": channels,
        "campaigns": campaigns,
        "has_data": bool(channels.get("channels") or campaigns.get("campaigns")),
    }
