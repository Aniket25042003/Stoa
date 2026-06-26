"""
File: services/core/src/stoa_core/alignment/friction.py
Layer: Core Alignment
Purpose: Cross-reference CRM outcomes with call/sales signals.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from stoa_core.db.supabase import get_supabase_admin


def collect_friction_signals(org_id: str) -> dict[str, Any]:
    """Gather objection and loss-theme signals for alignment narrative."""
    sb = get_supabase_admin()
    signals_res = (
        sb.table("intelligence")
        .select("kind, content")
        .eq("org_id", org_id)
        .in_("kind", ["objection", "pain_point", "buying_trigger"])
        .order("created_at", desc=True)
        .limit(100)
        .execute()
    )
    signals = signals_res.data or []

    deals_res = (
        sb.table("canonical_deals")
        .select("loss_reason")
        .eq("org_id", org_id)
        .eq("is_closed", True)
        .eq("is_won", False)
        .limit(200)
        .execute()
    )
    loss_reasons = Counter(
        d["loss_reason"] for d in (deals_res.data or []) if d.get("loss_reason")
    )

    objections = [s["content"][:200] for s in signals if s.get("kind") == "objection"][:5]
    pains = [s["content"][:200] for s in signals if s.get("kind") == "pain_point"][:5]

    return {
        "top_objections": objections,
        "top_pain_points": pains,
        "top_loss_reasons": [{"reason": k, "count": v} for k, v in loss_reasons.most_common(5)],
    }
