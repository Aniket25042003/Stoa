"""
File: services/api/app/tasks/enrichment.py
Layer: Celery Task Layer
Purpose: Agent memory enrichment — company/competitor research, checkpoints, scheduled maintenance.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.celery_app import celery_app
from app.services.audit import write_audit
from app.services.task_context import verify_competitor, verify_conversation_org, verify_org_exists
from app.tasks.competitive import monitor_competitor
from app.tasks.intelligence import precompute_insights
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.enrichment.jobs import (
    cleanup_stale_jobs,
    create_enrichment_job,
    mark_job_completed,
    mark_job_failed,
    mark_job_running,
)
from stoa_core.enrichment.pipeline import (
    run_company_enrichment,
    run_competitor_enrichment,
    seed_competitors_from_notes,
)
from stoa_core.enrichment.conversation import maybe_checkpoint_conversation
from stoa_core.enrichment.integrations import synthesize_crm_summary, synthesize_review_themes
from stoa_core.insights.dynamic import generate_dynamic_insights_for_org
from stoa_core.redis.client import publish_event
from stoa_core.security.client_errors import client_safe_error_message

logger = logging.getLogger(__name__)


def _run_job(org_id: str, job_type: str, *, target_id: str | None, idempotency_key: str | None, fn) -> dict:
    job = create_enrichment_job(
        org_id,
        job_type=job_type,
        target_id=target_id,
        idempotency_key=idempotency_key,
    )
    if not job:
        return {"skipped": True, "reason": "daily_cap_or_duplicate"}
    job_id = job["id"]
    publish_event("enrichment", org_id, {"status": "running", "job_id": job_id, "job_type": job_type})
    mark_job_running(job_id)
    try:
        result = fn()
        mark_job_completed(job_id, result)
        publish_event("enrichment", org_id, {"status": "completed", "job_id": job_id, "job_type": job_type})
        return result
    except Exception as exc:
        mark_job_failed(job_id, str(exc))
        safe_error = client_safe_error_message(str(exc), context="enrichment") or "Enrichment failed."
        publish_event(
            "enrichment",
            org_id,
            {"status": "failed", "job_id": job_id, "error": safe_error},
        )
        raise


@celery_app.task(name="enrichment.enrich_company", bind=True, max_retries=2)
def enrich_company(
    self,
    org_id: str,
    *,
    user_id: str | None = None,
    idempotency_suffix: str = "default",
) -> dict:
    try:
        verify_org_exists(org_id)

        def _work() -> dict:
            result = run_company_enrichment(org_id)
            write_audit(org_id, user_id, "enrichment.company_completed", "organization", org_id, result)
            precompute_insights.delay(org_id, force=True)
            generate_dynamic_insights_for_org(org_id)
            return result

        return _run_job(
            org_id,
            "company_enrichment",
            target_id=org_id,
            idempotency_key=f"company_enrichment:{org_id}:{idempotency_suffix}",
            fn=_work,
        )
    except Exception as exc:
        logger.exception("Company enrichment failed for org %s", org_id)
        raise self.retry(exc=exc, countdown=120) from exc


@celery_app.task(name="enrichment.enrich_competitor", bind=True, max_retries=2)
def enrich_competitor(self, org_id: str, competitor_id: str, *, user_id: str | None = None) -> dict:
    try:
        row = verify_competitor(competitor_id)
        if row["org_id"] != org_id:
            raise ValueError("Competitor org mismatch")

        def _work() -> dict:
            result = run_competitor_enrichment(org_id, competitor_id)
            write_audit(
                org_id,
                user_id,
                "enrichment.competitor_completed",
                "competitor",
                competitor_id,
                result,
            )
            return result

        return _run_job(
            org_id,
            "competitor_enrichment",
            target_id=competitor_id,
            idempotency_key=f"competitor_enrichment:{competitor_id}",
            fn=_work,
        )
    except Exception as exc:
        logger.exception("Competitor enrichment failed %s", competitor_id)
        raise self.retry(exc=exc, countdown=120) from exc


@celery_app.task(name="enrichment.seed_competitors_from_onboarding", bind=True, max_retries=1)
def seed_competitors_from_onboarding(self, org_id: str, notes: str, *, user_id: str | None = None) -> dict:
    try:
        verify_org_exists(org_id)
        ids = seed_competitors_from_notes(org_id, notes, created_by=user_id)
        for comp_id in ids:
            enrich_competitor.delay(org_id, comp_id, user_id=user_id)
            monitor_competitor.delay(comp_id)
        return {"competitor_ids": ids}
    except Exception as exc:
        logger.exception("Competitor seeding failed for org %s", org_id)
        raise self.retry(exc=exc, countdown=60) from exc


@celery_app.task(name="enrichment.checkpoint_conversation", bind=True, max_retries=2)
def checkpoint_conversation(self, org_id: str, conversation_id: str) -> dict:
    try:
        verify_conversation_org(conversation_id, org_id)

        def _work() -> dict:
            return maybe_checkpoint_conversation(org_id, conversation_id)

        return _run_job(
            org_id,
            "conversation_checkpoint",
            target_id=conversation_id,
            idempotency_key=f"conversation_checkpoint:{conversation_id}",
            fn=_work,
        )
    except Exception as exc:
        logger.exception("Conversation checkpoint failed %s", conversation_id)
        raise self.retry(exc=exc, countdown=60) from exc


@celery_app.task(name="enrichment.synthesize_crm_summary", bind=True, max_retries=2)
def enrich_crm_summary(self, org_id: str) -> dict:
    try:
        verify_org_exists(org_id)

        def _work() -> dict:
            return synthesize_crm_summary(org_id)

        return _run_job(
            org_id,
            "crm_summary",
            target_id=org_id,
            idempotency_key=f"crm_summary:{org_id}",
            fn=_work,
        )
    except Exception as exc:
        logger.exception("CRM summary enrichment failed for org %s", org_id)
        raise self.retry(exc=exc, countdown=120) from exc


@celery_app.task(name="enrichment.synthesize_review_themes", bind=True, max_retries=2)
def enrich_review_themes(self, org_id: str) -> dict:
    try:
        verify_org_exists(org_id)

        def _work() -> dict:
            return synthesize_review_themes(org_id)

        return _run_job(
            org_id,
            "review_themes",
            target_id=org_id,
            idempotency_key=f"review_themes:{org_id}",
            fn=_work,
        )
    except Exception as exc:
        logger.exception("Review themes enrichment failed for org %s", org_id)
        raise self.retry(exc=exc, countdown=120) from exc


@celery_app.task(name="enrichment.schedule_competitor_rescans")
def schedule_competitor_rescans() -> dict:
    sb = get_supabase_admin()
    res = sb.table("competitors").select("id, org_id").execute()
    queued = 0
    for row in res.data or []:
        monitor_competitor.delay(row["id"])
        enrich_competitor.delay(row["org_id"], row["id"])
        queued += 1
    logger.info("Scheduled %s competitor rescans", queued)
    return {"queued": queued}


@celery_app.task(name="enrichment.cleanup_stale_jobs")
def cleanup_stale_enrichment_jobs() -> dict:
    count = cleanup_stale_jobs()
    return {"failed_stale": count}


@celery_app.task(name="intelligence.schedule_precompute")
def schedule_precompute() -> dict:
    sb = get_supabase_admin()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    res = (
        sb.table("knowledge_items")
        .select("org_id")
        .gte("updated_at", cutoff)
        .execute()
    )
    org_ids = {row["org_id"] for row in (res.data or []) if row.get("org_id")}
    for org_id in org_ids:
        precompute_insights.delay(org_id, force=True)
    return {"orgs_scheduled": len(org_ids)}


@celery_app.task(name="integrations.schedule_syncs")
def schedule_integration_syncs() -> dict:
    sb = get_supabase_admin()
    res = (
        sb.table("integration_connections")
        .select("id, org_id")
        .eq("status", "active")
        .execute()
    )
    from app.tasks.integrations import sync_integration_source

    queued = 0
    for row in res.data or []:
        sync_integration_source.delay(row["id"], row["org_id"])
        queued += 1
    return {"queued": queued}
