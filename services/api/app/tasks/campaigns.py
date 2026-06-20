"""
File: services/api/app/tasks/campaigns.py
Layer: Celery Task Layer
Purpose: Runs background work that precomputes intelligence and updates durable job state.
Dependencies: Supabase, Celery, Redis, stoa_core
"""

from __future__ import annotations

import logging

from app.celery_app import celery_app
from app.services.task_context import verify_campaign
from stoa_core.campaign.generate import generate_campaign_assets
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.rag.ingest import ingest_knowledge, json_artifact_to_text
from stoa_core.rag.retrieve import retrieve_context
from stoa_core.redis.client import publish_event
from stoa_core.security.pii import redact_pii

logger = logging.getLogger(__name__)

CAMPAIGN_KINDS = [
    "company_profile",
    "icp_profile",
    "competitive_snapshot",
    "document",
    "campaign_asset",
]


@celery_app.task(name="campaigns.generate", bind=True, max_retries=2)
def generate_campaign(self, campaign_id: str) -> None:
    """Handles generate campaign logic for the surrounding Stoa workflow.

    Args:
        campaign_id (str): Input value used by this workflow step.
    """
    sb = get_supabase_admin()
    try:
        campaign = verify_campaign(campaign_id)
    except ValueError as exc:
        logger.warning("Rejected campaign generation %s: %s", campaign_id, exc)
        return

    org_id = campaign["org_id"]
    sb.table("campaigns").update({"status": "running"}).eq("id", campaign_id).execute()
    try:
        icp_res = (
            sb.table("icp_profiles").select("profile").eq("org_id", org_id).order("version", desc=True).limit(1).execute()
        )
        icp = (icp_res.data or [{}])[0].get("profile")
        alerts_res = (
            sb.table("competitive_alerts")
            .select("summary, severity")
            .eq("org_id", org_id)
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        brief = redact_pii(campaign["brief"])
        kb_context = retrieve_context(org_id, brief, kinds=CAMPAIGN_KINDS)
        kb_text = "\n".join(f"[{c['ref']}] {c['text'][:400]}" for c in kb_context[:12])

        assets = generate_campaign_assets(
            brief,
            icp_context=icp,
            competitive_context=alerts_res.data or [],
            brand_voice=campaign.get("brand_voice"),
            knowledge_context=kb_text,
        )
        if not assets:
            logger.error("Campaign %s generation returned no assets (LLM unavailable?)", campaign_id)
            sb.table("campaigns").update(
                {"status": "failed", "error": "generation returned no assets"}
            ).eq("id", campaign_id).execute()
            publish_event("campaign", campaign_id, {"status": "failed"})
            return
        sb.table("campaigns").update({"status": "completed", "assets": assets}).eq("id", campaign_id).execute()

        if assets:
            ingest_knowledge(
                org_id,
                kind="campaign_asset",
                title=f"Campaign: {brief[:80]}",
                text=json_artifact_to_text(assets),
                feature_origin="campaigns",
                uri=f"campaign:{campaign_id}",
                metadata={"campaign_id": campaign_id, "brief": brief[:500]},
            )

        publish_event("campaign", campaign_id, {"status": "completed"})
    except Exception as exc:
        logger.exception("Campaign generation failed %s", campaign_id)
        sb.table("campaigns").update({"status": "failed", "error": "generation failed"}).eq("id", campaign_id).execute()
        raise self.retry(exc=exc, countdown=60) from exc
