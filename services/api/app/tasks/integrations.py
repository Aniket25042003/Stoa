from __future__ import annotations

import logging

from app.celery_app import celery_app
from app.services.task_context import verify_org_exists
from app.tasks.intelligence import precompute_insights, rebuild_icp_profile
from stoa_core.integrations.service import run_sync

logger = logging.getLogger(__name__)


@celery_app.task(name="integrations.sync_source", bind=True, max_retries=2)
def sync_integration_source(
    self,
    connection_id: str,
    org_id: str,
    *,
    full_backfill: bool = False,
) -> dict:
    try:
        verify_org_exists(org_id)
        result = run_sync(connection_id, org_id, full_backfill=full_backfill)
        if result.get("records_written", 0) > 0 and not result.get("error"):
            rebuild_icp_profile.delay(org_id)
            precompute_insights.delay(org_id, force=True)
        return result
    except Exception as exc:
        logger.exception("Integration sync task failed for %s", connection_id)
        raise self.retry(exc=exc, countdown=120) from exc
