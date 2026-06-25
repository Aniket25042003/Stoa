"""
File: services/api/app/tasks/alignment.py
Layer: Celery Task Layer
Purpose: Precompute sales–marketing alignment insights.
"""

from __future__ import annotations

import logging

from app.celery_app import celery_app
from app.services.task_context import verify_org_exists
from stoa_core.alignment.aggregate import build_alignment_summary
from stoa_core.alignment.synthesize import precompute_alignment_answers
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.redis.client import publish_event

logger = logging.getLogger(__name__)


def _upsert_insight(org_id: str, item: dict, record_count: int) -> None:
    sb = get_supabase_admin()
    sb.table("precomputed_insights").upsert(
        {
            "org_id": org_id,
            "scope": "alignment",
            "key": item["key"],
            "title": item["title"],
            "content": item["content"],
            "citations": item.get("citations", []),
            "is_stale": False,
            "source_document_count": record_count,
        },
        on_conflict="org_id,scope,key",
    ).execute()


@celery_app.task(name="alignment.precompute", bind=True, max_retries=2)
def precompute_alignment(self, org_id: str, *, force: bool = False) -> None:
    """Precompute alignment insights for an org."""
    try:
        verify_org_exists(org_id)
        summary = build_alignment_summary(org_id)
        if not summary.get("has_data") and not force:
            logger.info("Skipping alignment precompute for org %s — no CRM data", org_id)
            publish_event("alignment", org_id, {"status": "skipped", "reason": "no_data"})
            return

        record_count = len(summary.get("lead_conversion", {}).get("by_source") or [])

        answers = precompute_alignment_answers(org_id)
        for item in answers:
            _upsert_insight(org_id, item, record_count)

        publish_event(
            "alignment",
            org_id,
            {"status": "completed", "insight_count": len(answers)},
        )
    except Exception as exc:
        logger.exception("Alignment precompute failed for org %s", org_id)
        publish_event("alignment", org_id, {"status": "failed"})
        raise self.retry(exc=exc, countdown=60) from exc
