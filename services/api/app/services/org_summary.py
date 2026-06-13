"""Shared org summary helpers for dashboard and org endpoints."""

from __future__ import annotations

from typing import Any

from stoa_core.db.supabase import get_supabase_admin
from stoa_core.org.completeness import compute_completeness


def fetch_org_counts(org_id: str) -> dict[str, int]:
    sb = get_supabase_admin()
    docs = sb.table("documents").select("id", count="exact").eq("org_id", org_id).execute()
    signals = sb.table("intelligence").select("id", count="exact").eq("org_id", org_id).execute()
    competitors = sb.table("competitors").select("id", count="exact").eq("org_id", org_id).execute()
    alerts = sb.table("competitive_alerts").select("id", count="exact").eq("org_id", org_id).execute()
    campaigns = sb.table("campaigns").select("id", count="exact").eq("org_id", org_id).execute()
    integrations = (
        sb.table("integration_connections")
        .select("id", count="exact")
        .eq("org_id", org_id)
        .eq("status", "active")
        .execute()
    )
    deals = sb.table("canonical_deals").select("id", count="exact").eq("org_id", org_id).execute()
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
    sb = get_supabase_admin()
    res = sb.table("intelligence").select("kind").eq("org_id", org_id).limit(500).execute()
    counts: dict[str, int] = {}
    for row in res.data or []:
        kind = row.get("kind") or "unknown"
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def latest_icp_version(org_id: str) -> int | None:
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


def build_completeness_for_org(
    org: dict[str, Any],
    *,
    counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    org_id = org["id"]
    resolved = counts or fetch_org_counts(org_id)
    return compute_completeness(
        org,
        document_count=resolved["documents"],
        competitor_count=resolved["competitors"],
        integration_count=resolved.get("integrations", 0),
        canonical_deal_count=resolved.get("canonical_deals", 0),
    )
