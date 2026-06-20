"""
File: services/api/app/tasks/competitive.py
Layer: Celery Task Layer
Purpose: Runs background work that precomputes intelligence and updates durable job state.
Dependencies: Supabase, Celery, Redis, stoa_core
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.celery_app import celery_app
from app.services.task_context import verify_competitor
from stoa_core.competitive.monitor import content_hash, detect_changes, fetch_page_text
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.rag.ingest import ingest_knowledge
from stoa_core.redis.client import publish_event
from stoa_core.security.pii import redact_pii

logger = logging.getLogger(__name__)


@celery_app.task(name="competitive.monitor", bind=True, max_retries=2)
def monitor_competitor(self, competitor_id: str) -> None:
    """Handles monitor competitor logic for the surrounding Stoa workflow.

    Args:
        competitor_id (str): Input value used by this workflow step.
    """
    sb = get_supabase_admin()
    try:
        comp = verify_competitor(competitor_id)
    except ValueError as exc:
        logger.warning("Rejected competitor monitor %s: %s", competitor_id, exc)
        return

    url = comp.get("website_url") or comp.get("pricing_url")
    if not url:
        return

    try:
        new_text = redact_pii(fetch_page_text(url))
        old_snap = comp.get("last_snapshot") or ""
        diff = detect_changes(old_snap, new_text, comp.get("name", "competitor"))
        new_hash = content_hash(new_text)
        snapshot = new_text[:20000]

        sb.table("competitors").update(
            {
                "content_hash": new_hash,
                "last_snapshot": snapshot,
                "last_scanned_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", competitor_id).execute()

        ingest_knowledge(
            comp["org_id"],
            kind="competitive_snapshot",
            title=f"{comp.get('name', 'Competitor')} snapshot",
            text=snapshot,
            feature_origin="competitive",
            uri=f"competitor:{competitor_id}",
            metadata={"competitor_id": competitor_id, "url": url},
        )

        if diff and diff.get("changed") is not False:
            summary = redact_pii(diff.get("summary", "Change detected") or "Change detected")
            sb.table("competitive_alerts").insert(
                {
                    "org_id": comp["org_id"],
                    "competitor_id": competitor_id,
                    "summary": summary,
                    "severity": diff.get("severity", "medium"),
                    "categories": diff.get("categories", []),
                }
            ).execute()
            publish_event("competitive", competitor_id, {"alert": {**diff, "summary": summary}})
    except Exception as exc:
        logger.exception("Competitor monitor failed %s", competitor_id)
        raise self.retry(exc=exc, countdown=120) from exc
