"""
File: services/api/app/tasks/campaign_analysis.py
Layer: Celery Task Layer
Purpose: Precompute campaign analysis insights.
"""

from __future__ import annotations

import logging

from app.celery_app import celery_app
from app.services.task_context import verify_org_exists
from stoa_core.analytics.aggregate import build_summary_metrics
from stoa_core.analytics.synthesize import precompute_campaign_answers
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.rag.ingest import ingest_knowledge
from stoa_core.redis.client import publish_event

logger = logging.getLogger(__name__)


def _upsert_insight(org_id: str, item: dict, metric_count: int) -> None:
    sb = get_supabase_admin()
    sb.table("precomputed_insights").upsert(
        {
            "org_id": org_id,
            "scope": "campaign_analysis",
            "key": item["key"],
            "title": item["title"],
            "content": item["content"],
            "citations": item.get("citations", []),
            "is_stale": False,
            "source_document_count": metric_count,
        },
        on_conflict="org_id,scope,key",
    ).execute()


@celery_app.task(name="campaign_analysis.precompute", bind=True, max_retries=2)
def precompute_campaign_analysis(self, org_id: str, *, force: bool = False) -> None:
    """Precompute campaign analysis insights for an org."""
    try:
        verify_org_exists(org_id)
        summary = build_summary_metrics(org_id)
        if not summary.get("has_data") and not force:
            logger.info("Skipping campaign analysis precompute for org %s — no metrics", org_id)
            publish_event("campaign_analysis", org_id, {"status": "skipped", "reason": "no_data"})
            return

        metric_count = len(summary.get("channels", {}).get("channels") or []) + len(
            summary.get("campaigns", {}).get("campaigns") or []
        )

        for item in precompute_campaign_answers(org_id):
            _upsert_insight(org_id, item, metric_count)

        ingest_knowledge(
            org_id,
            kind="campaign_metrics",
            title="Campaign analysis snapshot",
            text=str(summary)[:8000],
            feature_origin="campaign_analysis",
            uri=f"campaign_analysis:snapshot:{org_id}",
            metadata={"metric_count": metric_count},
        )

        publish_event(
            "campaign_analysis",
            org_id,
            {"status": "completed", "insight_count": metric_count},
        )
    except Exception as exc:
        logger.exception("Campaign analysis precompute failed for org %s", org_id)
        publish_event("campaign_analysis", org_id, {"status": "failed"})
        raise self.retry(exc=exc, countdown=60) from exc
