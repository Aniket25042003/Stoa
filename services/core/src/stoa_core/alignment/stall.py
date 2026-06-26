"""
File: services/core/src/stoa_core/alignment/stall.py
Layer: Core Alignment
Purpose: Deal stall detection by pipeline stage.
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any

from stoa_core.db.supabase import get_supabase_admin

STALL_DAYS = 30


def aggregate_stall_points(org_id: str) -> dict[str, Any]:
    """Find open deals stalled in stage for > STALL_DAYS days."""
    sb = get_supabase_admin()
    res = (
        sb.table("canonical_deals")
        .select("id, name, stage, updated_at, created_at, is_closed")
        .eq("org_id", org_id)
        .eq("is_closed", False)
        .limit(500)
        .execute()
    )
    deals = res.data or []
    now = datetime.now(UTC)
    stalled_by_stage: Counter[str] = Counter()
    stalled_deals: list[dict[str, Any]] = []

    for d in deals:
        ts = d.get("updated_at") or d.get("created_at")
        if not ts:
            continue
        try:
            if isinstance(ts, str):
                updated = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            else:
                updated = ts
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=UTC)
        except (ValueError, TypeError):
            continue
        days_open = (now - updated).days
        if days_open >= STALL_DAYS:
            stage = d.get("stage") or "Unknown"
            stalled_by_stage[stage] += 1
            if len(stalled_deals) < 10:
                stalled_deals.append(
                    {
                        "deal_id": d["id"],
                        "name": d.get("name"),
                        "stage": stage,
                        "days_in_stage": days_open,
                    }
                )

    stages = [
        {"stage": stage, "stalled_count": count}
        for stage, count in stalled_by_stage.most_common(5)
    ]
    return {
        "stalled_deals": stalled_deals,
        "top_stall_stages": stages,
        "stall_threshold_days": STALL_DAYS,
    }
