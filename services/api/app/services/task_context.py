"""Validate Celery task arguments against database ownership."""

from __future__ import annotations

import uuid

from stoa_core.db.supabase import get_supabase_admin

ALLOWED_CELERY_TASKS = frozenset(
    {
        "ingestion.process_job",
        "intelligence.precompute_insights",
        "intelligence.rebuild_icp",
        "intelligence.answer_question",
        "competitive.monitor",
        "campaigns.generate",
        "knowledge.reembed_org",
    }
)


def assert_allowed_task(task_name: str) -> None:
    if task_name not in ALLOWED_CELERY_TASKS:
        raise ValueError(f"Disallowed Celery task: {task_name}")


def _parse_uuid(value: str, field: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field}: {value}") from exc


def verify_org_exists(org_id: str) -> None:
    org_id = _parse_uuid(org_id, "org_id")
    sb = get_supabase_admin()
    res = sb.table("organizations").select("id").eq("id", org_id).limit(1).execute()
    if not res.data:
        raise ValueError(f"Unknown organization: {org_id}")


def verify_resource_org(table: str, resource_id: str, org_id: str | None = None, *, id_column: str = "id") -> dict:
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
