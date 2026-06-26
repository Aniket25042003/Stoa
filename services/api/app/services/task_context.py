"""
File: services/api/app/services/task_context.py
Layer: FastAPI Service Layer
Purpose: Contains reusable backend business logic shared by routes and workers.
Dependencies: Supabase, Celery, stoa_core
"""


from __future__ import annotations

import uuid

from stoa_core.db.supabase import get_supabase_admin

ALLOWED_CELERY_TASKS = frozenset(
    {
        "ingestion.process_job",
        "intelligence.precompute_insights",
        "intelligence.rebuild_icp",
        "intelligence.answer_question",
        "intelligence.schedule_precompute",
        "competitive.monitor",
        "campaigns.generate",
        "content.generate_asset",
        "knowledge.reembed_org",
        "integrations.sync_source",
        "integrations.schedule_syncs",
        "enrichment.enrich_company",
        "enrichment.enrich_competitor",
        "enrichment.seed_competitors_from_onboarding",
        "enrichment.checkpoint_conversation",
        "enrichment.synthesize_crm_summary",
        "enrichment.synthesize_review_themes",
        "enrichment.schedule_competitor_rescans",
        "enrichment.cleanup_stale_jobs",
    }
)


def assert_allowed_task(task_name: str) -> None:
    """Handles assert allowed task logic for the surrounding Stoa workflow.

    Args:
        task_name (str): Input value used by this workflow step.
    """
    if task_name not in ALLOWED_CELERY_TASKS:
        raise ValueError(f"Disallowed Celery task: {task_name}")


def _parse_uuid(value: str, field: str) -> str:
    """Handles  parse uuid logic for the surrounding Stoa workflow.

    Args:
        value (str): Input value used by this workflow step.
        field (str): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field}: {value}") from exc


def verify_org_exists(org_id: str) -> None:
    """Handles verify org exists logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.
    """
    org_id = _parse_uuid(org_id, "org_id")
    sb = get_supabase_admin()
    res = sb.table("organizations").select("id").eq("id", org_id).limit(1).execute()
    if not res.data:
        raise ValueError(f"Unknown organization: {org_id}")


def verify_resource_org(table: str, resource_id: str, org_id: str | None = None, *, id_column: str = "id") -> dict:
    """Handles verify resource org logic for the surrounding Stoa workflow.

    Args:
        table (str): Input value used by this workflow step.
        resource_id (str): Input value used by this workflow step.
        org_id (str | None): Input value used by this workflow step.
        id_column (str): Input value used by this workflow step.

    Returns:
        dict: Result produced for the caller.
    """
    resource_id = _parse_uuid(resource_id, f"{table}_id")
    if org_id is not None:
        org_id = _parse_uuid(org_id, "org_id")
    sb = get_supabase_admin()
    res = sb.table(table).select("id, org_id").eq(id_column, resource_id).limit(1).execute()
    row = (res.data or [None])[0]
    if not row:
        raise ValueError(f"{table} resource not found: {resource_id}")
    if org_id is not None and row.get("org_id") != org_id:
        raise ValueError(f"{table} resource {resource_id} does not belong to org {org_id}")
    return row


def verify_conversation_org(conversation_id: str, org_id: str) -> dict:
    """Handles verify conversation org logic for the surrounding Stoa workflow.

    Args:
        conversation_id (str): Input value used by this workflow step.
        org_id (str): Input value used by this workflow step.

    Returns:
        dict: Result produced for the caller.
    """
    return verify_resource_org("conversations", conversation_id, org_id)


def verify_ingestion_job(job_id: str) -> tuple[dict, dict]:
    """Load job + document and ensure org consistency. Returns (job, document)."""
    job_id = _parse_uuid(job_id, "job_id")
    sb = get_supabase_admin()
    job_res = sb.table("ingestion_jobs").select("id, org_id, document_id, status").eq("id", job_id).limit(1).execute()
    job = (job_res.data or [None])[0]
    if not job:
        raise ValueError(f"Ingestion job not found: {job_id}")

    doc_res = (
        sb.table("documents")
        .select("id, org_id, content, title, doc_type")
        .eq("id", job["document_id"])
        .limit(1)
        .execute()
    )
    doc = (doc_res.data or [None])[0]
    if not doc:
        raise ValueError(f"Document not found for job: {job_id}")
    if doc["org_id"] != job["org_id"]:
        raise ValueError(f"Job {job_id} org mismatch with document {doc['id']}")
    return job, doc


def verify_competitor(competitor_id: str) -> dict:
    """Handles verify competitor logic for the surrounding Stoa workflow.

    Args:
        competitor_id (str): Input value used by this workflow step.

    Returns:
        dict: Result produced for the caller.
    """
    competitor_id = _parse_uuid(competitor_id, "competitor_id")
    sb = get_supabase_admin()
    res = (
        sb.table("competitors")
        .select("id, org_id, name, website_url, pricing_url, content_hash, last_snapshot")
        .eq("id", competitor_id)
        .limit(1)
        .execute()
    )
    row = (res.data or [None])[0]
    if not row:
        raise ValueError(f"Competitor not found: {competitor_id}")
    return row


def verify_campaign(campaign_id: str) -> dict:
    """Handles verify campaign logic for the surrounding Stoa workflow.

    Args:
        campaign_id (str): Input value used by this workflow step.

    Returns:
        dict: Result produced for the caller.
    """
    campaign_id = _parse_uuid(campaign_id, "campaign_id")
    sb = get_supabase_admin()
    res = (
        sb.table("campaigns")
        .select("id, org_id, brief, brand_voice, status")
        .eq("id", campaign_id)
        .limit(1)
        .execute()
    )
    row = (res.data or [None])[0]
    if not row:
        raise ValueError(f"Campaign not found: {campaign_id}")
    return row


def verify_content_asset(asset_id: str, org_id: str | None = None) -> dict:
    """Loads and verifies a content asset resource.

    Args:
        asset_id (str): UUID of the content asset.
        org_id (str | None): When set, assert the asset belongs to this org.

    Returns:
        dict: The content asset row from the database.
    """
    asset_id = _parse_uuid(asset_id, "asset_id")
    if org_id is not None:
        org_id = _parse_uuid(org_id, "org_id")
    sb = get_supabase_admin()
    res = (
        sb.table("content_assets")
        .select("id, org_id, campaign_id, asset_type, prompt, config, status, reference_asset_id, files")
        .eq("id", asset_id)
        .limit(1)
        .execute()
    )
    row = (res.data or [None])[0]
    if not row:
        raise ValueError(f"Content asset not found: {asset_id}")
    if org_id is not None and row.get("org_id") != org_id:
        raise ValueError(f"Content asset {asset_id} does not belong to org {org_id}")
    return row
