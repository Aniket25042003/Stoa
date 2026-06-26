"""
File: services/core/src/stoa_core/alignment/aggregate.py
Layer: Core Alignment
Purpose: Lead quality and revenue attribution aggregations.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from stoa_core.db.supabase import get_supabase_admin


def _load_contacts(org_id: str) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    res = (
        sb.table("canonical_contacts")
        .select("id, lead_source, utm_campaign, utm_source, title, account_id")
        .eq("org_id", org_id)
        .limit(500)
        .execute()
    )
    return res.data or []


def _load_deals(org_id: str) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    res = (
        sb.table("canonical_deals")
        .select(
            "id, amount, stage, is_won, is_closed, loss_reason, "
            "lead_source, utm_campaign, account_id, updated_at, created_at"
        )
        .eq("org_id", org_id)
        .limit(500)
        .execute()
    )
    return res.data or []


def aggregate_lead_conversion(org_id: str) -> dict[str, Any]:
    """Close rate by lead source."""
    contacts = _load_contacts(org_id)
    deals = _load_deals(org_id)
    if not contacts and not deals:
        return {"by_source": [], "top_source": None}

    account_to_source: dict[str, str] = {}
    for c in contacts:
        if c.get("account_id") and c.get("lead_source"):
            account_to_source[c["account_id"]] = c["lead_source"]

    by_source: dict[str, dict[str, int | float]] = defaultdict(
        lambda: {"leads": 0, "won": 0, "lost": 0, "open": 0, "revenue": 0.0}
    )
    for c in contacts:
        src = c.get("lead_source") or c.get("utm_campaign") or "Unknown"
        by_source[src]["leads"] += 1

    for d in deals:
        src = (
            d.get("lead_source")
            or d.get("utm_campaign")
            or account_to_source.get(d.get("account_id") or "", "")
            or "Unknown"
        )
        if d.get("is_won") is True:
            by_source[src]["won"] += 1
            by_source[src]["revenue"] += float(d.get("amount") or 0)
        elif d.get("is_closed") is True:
            by_source[src]["lost"] += 1
        else:
            by_source[src]["open"] += 1

    rows = []
    for source, vals in by_source.items():
        total_closed = int(vals["won"]) + int(vals["lost"])
        close_rate = round(int(vals["won"]) / total_closed * 100, 1) if total_closed > 0 else None
        rows.append(
            {
                "source": source,
                "leads": int(vals["leads"]),
                "won": int(vals["won"]),
                "lost": int(vals["lost"]),
                "open": int(vals["open"]),
                "revenue": round(float(vals["revenue"]), 2),
                "close_rate_percent": close_rate,
            }
        )
    rows.sort(key=lambda r: r["revenue"], reverse=True)
    return {"by_source": rows, "top_source": rows[0] if rows else None}


def aggregate_campaign_revenue(org_id: str) -> dict[str, Any]:
    """Revenue attributed to UTM campaigns."""
    deals = _load_deals(org_id)
    by_campaign: dict[str, float] = defaultdict(float)
    counts: Counter[str] = Counter()
    for d in deals:
        campaign = d.get("utm_campaign")
        if not campaign:
            continue
        counts[campaign] += 1
        if d.get("is_won") is True and d.get("amount") is not None:
            by_campaign[campaign] += float(d["amount"])

    campaigns = [
        {"campaign": k, "deals": counts[k], "revenue": round(by_campaign[k], 2)}
        for k in sorted(by_campaign, key=lambda x: by_campaign[x], reverse=True)
    ]
    return {"campaigns": campaigns, "top_campaign": campaigns[0] if campaigns else None}


def build_alignment_summary(org_id: str) -> dict[str, Any]:
    """Combined alignment metrics for API and synthesis."""
    lead_data = aggregate_lead_conversion(org_id)
    campaign_data = aggregate_campaign_revenue(org_id)
    from stoa_core.alignment.stall import aggregate_stall_points

    stall_data = aggregate_stall_points(org_id)
    has_data = bool(lead_data.get("by_source") or campaign_data.get("campaigns"))
    return {
        "lead_conversion": lead_data,
        "campaign_revenue": campaign_data,
        "stall_points": stall_data,
        "has_data": has_data,
    }
