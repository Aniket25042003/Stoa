"""
File: services/api/app/tasks/integrations.py
Layer: Celery Task Layer
Purpose: Runs background work that precomputes intelligence and updates durable job state.
Dependencies: Celery, stoa_core
"""

from __future__ import annotations

import logging

from app.celery_app import celery_app
from app.services.task_context import verify_org_exists
from app.tasks.alignment import precompute_alignment
from app.tasks.campaign_analysis import precompute_campaign_analysis
from app.tasks.intelligence import precompute_insights, rebuild_icp_profile
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.integrations.service import run_sync

logger = logging.getLogger(__name__)

_ANALYTICS_PROVIDERS = frozenset({"ga4", "posthog"})
_CRM_PROVIDERS = frozenset({"hubspot", "salesforce"})


@celery_app.task(name="integrations.sync_source", bind=True, max_retries=2)
def sync_integration_source(
    self,
    connection_id: str,
    org_id: str,
    *,
    full_backfill: bool = False,
) -> dict:
    """Handles sync integration source logic for the surrounding Stoa workflow."""
    try:
        verify_org_exists(org_id)
        sb = get_supabase_admin()
        conn_res = (
            sb.table("integration_connections")
            .select("provider")
            .eq("id", connection_id)
            .eq("org_id", org_id)
            .limit(1)
            .execute()
        )
        provider = (conn_res.data or [{}])[0].get("provider")

        result = run_sync(connection_id, org_id, full_backfill=full_backfill)
        if result.get("records_written", 0) > 0 and not result.get("error"):
            rebuild_icp_profile.delay(org_id)
            precompute_insights.delay(org_id, force=True)
            if provider in _ANALYTICS_PROVIDERS:
                precompute_campaign_analysis.delay(org_id)
            if provider in _CRM_PROVIDERS:
                precompute_alignment.delay(org_id)
        return result
    except Exception as exc:
        logger.exception("Integration sync task failed for %s", connection_id)
        raise self.retry(exc=exc, countdown=120) from exc
