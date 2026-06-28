"""Lazy Celery enqueue helpers for agent refresh tools (API worker runtime)."""

from __future__ import annotations

import logging
from typing import Any

from stoa_core.db.supabase import get_supabase_admin
from stoa_core.integrations.service import list_connections

logger = logging.getLogger(__name__)


def _find_connection(org_id: str, provider: str) -> dict[str, Any] | None:
    for conn in list_connections(org_id):
        if conn.get("provider") == provider and conn.get("status") not in {
            "revoked",
            "disconnected",
        }:
            return conn
    return None


def enqueue_refresh_connected_source(
    org_id: str,
    provider: str,
    *,
    full_backfill: bool = False,
) -> dict[str, Any]:
    conn = _find_connection(org_id, provider)
    if not conn:
        return {"status": "error", "error": f"No active {provider} connection"}
    connection_id = str(conn["id"])
    try:
        from app.tasks.integrations import sync_integration_source

        sync_integration_source.delay(connection_id, org_id, full_backfill=full_backfill)
        return {
            "status": "queued",
            "connection_id": connection_id,
            "provider": provider,
            "job": "integration.sync",
        }
    except ImportError:
        logger.warning("Celery tasks unavailable for refresh_connected_source")
        return {"status": "error", "error": "Background refresh unavailable in this runtime"}


def enqueue_refresh_precomputed_insights(org_id: str, scope: str | None = None) -> dict[str, Any]:
    try:
        from app.tasks.intelligence import precompute_insights

        precompute_insights.delay(org_id, force=True)
        return {
            "status": "queued",
            "job": "intelligence.precompute_insights",
            "scope": scope or "all",
        }
    except ImportError:
        return {"status": "error", "error": "Background refresh unavailable in this runtime"}


def enqueue_refresh_competitor_intel(
    org_id: str,
    competitor_name: str | None = None,
) -> dict[str, Any]:
    sb = get_supabase_admin()
    q = sb.table("competitors").select("id, name").eq("org_id", org_id)
    if competitor_name:
        q = q.ilike("name", f"%{competitor_name.strip()}%")
    res = q.order("created_at", desc=True).limit(1).execute()
    row = (res.data or [None])[0]
    if not row:
        return {"status": "error", "error": "No matching competitor found"}

    competitor_id = str(row["id"])
    try:
        from app.tasks.competitive import monitor_competitor
        from app.tasks.enrichment import enrich_competitor

        monitor_competitor.delay(competitor_id)
        enrich_competitor.delay(org_id, competitor_id)
        return {
            "status": "queued",
            "competitor_id": competitor_id,
            "competitor_name": row.get("name"),
            "jobs": ["competitive.monitor", "enrichment.enrich_competitor"],
        }
    except ImportError:
        return {"status": "error", "error": "Background refresh unavailable in this runtime"}
