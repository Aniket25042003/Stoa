"""Shared document create + ingestion job queue (storage, DB, RAG pipeline)."""

from __future__ import annotations

import uuid
from typing import Any

from stoa_core.config import get_settings
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.security.pii import redact_pii
from stoa_core.security.sanitize import sanitize_user_content
from stoa_core.security.urls import safe_storage_filename


def document_quota_exceeded(org_id: str) -> bool:
    settings = get_settings()
    sb = get_supabase_admin()
    doc_count = sb.table("documents").select("id", count="exact").eq("org_id", org_id).execute()
    return (doc_count.count or 0) >= settings.max_documents_per_org


def queue_text_document(
    *,
    org_id: str,
    user_id: str,
    title: str,
    content: str,
    doc_type: str = "note",
    feature_origin: str = "intelligence",
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Persist pasted text to documents and enqueue Celery ingestion (→ unified KB embeddings)."""
    if document_quota_exceeded(org_id):
        raise ValueError("Document quota exceeded")

    sb = get_supabase_admin()
    text = redact_pii(sanitize_user_content(content))
    doc_id = str(uuid.uuid4())
    doc_res = (
        sb.table("documents")
        .insert(
            {
                "id": doc_id,
                "org_id": org_id,
                "title": title,
                "doc_type": doc_type,
                "content": text,
                "created_by": user_id,
            }
        )
        .execute()
    )
    job = _insert_job(sb, org_id, doc_id, user_id)
    _dispatch_job(job)
    return (doc_res.data or [None])[0], job


def queue_uploaded_document(
    *,
    org_id: str,
    user_id: str,
    title: str,
    doc_type: str,
    filename: str,
    raw_bytes: bytes,
    text: str,
    feature_origin: str = "intelligence",
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Upload bytes to storage, persist document row, enqueue ingestion."""
    if document_quota_exceeded(org_id):
        raise ValueError("Document quota exceeded")

    settings = get_settings()
    sb = get_supabase_admin()
    doc_id = str(uuid.uuid4())
    safe_name = safe_storage_filename(filename or "upload.txt")
    storage_path = f"{org_id}/{doc_id}/{safe_name}"
    sb.storage.from_(settings.storage_bucket).upload(storage_path, raw_bytes)

    doc_res = (
        sb.table("documents")
        .insert(
            {
                "id": doc_id,
                "org_id": org_id,
                "title": title,
                "doc_type": doc_type,
                "content": text,
                "storage_path": storage_path,
                "created_by": user_id,
            }
        )
        .execute()
    )
    job = _insert_job(sb, org_id, doc_id, user_id)
    _dispatch_job(job)
    return (doc_res.data or [None])[0], job


def _insert_job(sb: Any, org_id: str, doc_id: str, user_id: str) -> dict[str, Any] | None:
    job_res = (
        sb.table("ingestion_jobs")
        .insert({"org_id": org_id, "document_id": doc_id, "status": "queued", "created_by": user_id})
        .execute()
    )
    return (job_res.data or [None])[0]


def _dispatch_job(job: dict[str, Any] | None) -> None:
    if not job:
        return
    from app.tasks.ingestion import process_ingestion_job

    process_ingestion_job.delay(job["id"])
