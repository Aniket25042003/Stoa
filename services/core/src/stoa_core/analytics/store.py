"""
File: services/core/src/stoa_core/analytics/store.py
Layer: Core Analytics
Purpose: Upsert structured analytics metric facts from integration syncs.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from stoa_core.db.supabase import get_supabase_admin


def upsert_metric_fact(
    org_id: str,
    *,
    connection_id: str | None,
    source: str,
    period_start: date,
    period_end: date,
    dimension_type: str,
    dimension_value: str,
    metrics: dict[str, Any],
) -> None:
    """Upsert a single analytics metric fact row."""
    sb = get_supabase_admin()
    sb.table("analytics_metric_facts").upsert(
        {
            "org_id": org_id,
            "connection_id": connection_id,
            "source": source,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "dimension_type": dimension_type,
            "dimension_value": dimension_value or "(not set)",
            "metrics": metrics,
        },
        on_conflict="org_id,source,period_start,period_end,dimension_type,dimension_value",
    ).execute()


def upsert_metric_facts_batch(
    org_id: str,
    *,
    connection_id: str | None,
    source: str,
    period_start: date,
    period_end: date,
    rows: list[dict[str, Any]],
) -> int:
    """Upsert multiple metric facts. Each row: dimension_type, dimension_value, metrics."""
    count = 0
    for row in rows:
        upsert_metric_fact(
            org_id,
            connection_id=connection_id,
            source=source,
            period_start=period_start,
            period_end=period_end,
            dimension_type=row["dimension_type"],
            dimension_value=row.get("dimension_value", ""),
            metrics=row.get("metrics", {}),
        )
        count += 1
    return count
