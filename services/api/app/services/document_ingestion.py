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


def get_document_for_org(org_id: str, document_id: str) -> dict[str, Any] | None:
    sb = get_supabase_admin()
    res = (
        sb.table("documents")
        .select("id, org_id, title, doc_type, status, content, storage_path, created_at, updated_at")
        .eq("id", document_id)
        .eq("org_id", org_id)
        .limit(1)
        .execute()
    )
    return (res.data or [None])[0]


def delete_document_for_org(org_id: str, document_id: str) -> bool:
    doc = get_document_for_org(org_id, document_id)
    if not doc:
        return False

    sb = get_supabase_admin()
    settings = get_settings()

    storage_path = doc.get("storage_path")
    if storage_path:
        try:
            sb.storage.from_(settings.storage_bucket).remove([storage_path])
        except Exception:
            pass

    sb.table("knowledge_items").delete().eq("org_id", org_id).eq("uri", f"document:{document_id}").execute()
    sb.table("intelligence").delete().eq("org_id", org_id).eq("document_id", document_id).execute()
    sb.table("document_chunks").delete().eq("org_id", org_id).eq("document_id", document_id).execute()
    sb.table("documents").delete().eq("id", document_id).eq("org_id", org_id).execute()
    return True


def is_pasted_document(doc: dict[str, Any]) -> bool:
    """Pasted documents have inline content only; uploads retain a storage_path."""
    return not doc.get("storage_path")


def update_pasted_document_for_org(
    org_id: str,
    document_id: str,
    user_id: str,
    *,
    title: str | None = None,
    content: str | None = None,
    doc_type: str | None = None,
) -> dict[str, Any]:
    doc = get_document_for_org(org_id, document_id)
    if not doc:
        raise ValueError("Document not found")
    if not is_pasted_document(doc):
        raise ValueError("Uploaded files cannot be edited in place")

    updates: dict[str, Any] = {"status": "pending"}
    if title is not None:
        title = title.strip()
        if not title:
            raise ValueError("Title is required")
        updates["title"] = title
    if doc_type is not None:
        updates["doc_type"] = doc_type
    if content is not None:
        if not content.strip():
            raise ValueError("Content is required")
        updates["content"] = redact_pii(sanitize_user_content(content))
    if len(updates) == 1:
        raise ValueError("No changes provided")

    sb = get_supabase_admin()
    sb.table("knowledge_items").delete().eq("org_id", org_id).eq("uri", f"document:{document_id}").execute()
    sb.table("intelligence").delete().eq("org_id", org_id).eq("document_id", document_id).execute()
    sb.table("document_chunks").delete().eq("org_id", org_id).eq("document_id", document_id).execute()

    res = sb.table("documents").update(updates).eq("id", document_id).eq("org_id", org_id).execute()
    updated = (res.data or [None])[0]
    if not updated:
        raise ValueError("Document not found")

    job = _insert_job(sb, org_id, document_id, user_id)
    _dispatch_job(job)
    return updated
