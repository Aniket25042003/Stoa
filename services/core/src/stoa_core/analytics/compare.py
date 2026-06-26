"""
File: services/core/src/stoa_core/analytics/compare.py
Layer: Core Analytics
Purpose: Compare two campaigns side-by-side.
"""

from __future__ import annotations

from typing import Any

from stoa_core.analytics.aggregate import aggregate_campaign_metrics


def compare_campaigns(org_id: str, campaign_a: str, campaign_b: str) -> dict[str, Any]:
    """Return side-by-side metrics for two campaigns."""
    data = aggregate_campaign_metrics(org_id)
    lookup = {c["campaign"]: c for c in data.get("campaigns") or []}
    a = lookup.get(campaign_a)
    b = lookup.get(campaign_b)
    if not a or not b:
        return {
            "campaign_a": a or {"campaign": campaign_a, "sessions": 0, "conversions": 0},
            "campaign_b": b or {"campaign": campaign_b, "sessions": 0, "conversions": 0},
            "delta_conversions": None,
            "delta_sessions": None,
            "found_both": bool(a and b),
        }
    return {
        "campaign_a": a,
        "campaign_b": b,
        "delta_conversions": a["conversions"] - b["conversions"],
        "delta_sessions": a["sessions"] - b["sessions"],
        "found_both": True,
    }
