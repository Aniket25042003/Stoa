from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.deps.auth import verify_supabase_jwt
from app.deps.rate_limit import check_rate_limit
from app.services.audit import write_audit
from app.services.org_context import get_user_membership, require_role
from app.tasks.ingestion import process_ingestion_job
from stoa_core.config import get_settings
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.security.pii import redact_pii
from stoa_core.security.sanitize import (
    UploadValidationError,
    sanitize_user_content,
    validate_doc_type,
    validate_upload,
)
from stoa_core.security.urls import safe_storage_filename

router = APIRouter(prefix="/v1/ingestion", tags=["ingestion"])


class PasteBody(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=1, max_length=10 * 1024 * 1024)
    doc_type: str = Field(default="note", pattern="^(call_transcript|review|crm_export|note)$")


def _document_quota_exceeded(org_id: str) -> bool:
    settings = get_settings()
    sb = get_supabase_admin()
    doc_count = sb.table("documents").select("id", count="exact").eq("org_id", org_id).execute()
    return (doc_count.count or 0) >= settings.max_documents_per_org


@router.get("/sources")
def list_sources(user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    sb = get_supabase_admin()
    res = (
        sb.table("data_sources")
        .select("id, org_id, name, source_type, status, created_at, updated_at")
        .eq("org_id", membership["org_id"])
        .order("created_at", desc=True)
        .execute()
    )
    return {"sources": res.data or []}


@router.post("/upload")
async def upload_document(
    title: str = Form(..., min_length=1, max_length=300),
    doc_type: str = Form("note"),
    file: UploadFile = File(...),
    user_id: str = Depends(verify_supabase_jwt),
) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    require_role(membership, "analyst")
    check_rate_limit(user_id, get_settings().rate_limit_per_minute, scope="upload")
    settings = get_settings()
    sb = get_supabase_admin()

    try:
        validate_doc_type(doc_type)
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = await file.read(64 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > settings.max_upload_bytes:
                raise UploadValidationError("File too large")
            chunks.append(chunk)
        content = b"".join(chunks)
        validate_upload(file.filename or "upload.txt", file.content_type, len(content), settings.max_upload_bytes)
    except UploadValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    text = redact_pii(sanitize_user_content(content.decode("utf-8", errors="replace")))

    if _document_quota_exceeded(membership["org_id"]):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Document quota exceeded")

    doc_id = str(uuid.uuid4())
    safe_name = safe_storage_filename(file.filename or "upload.txt")
    storage_path = f"{membership['org_id']}/{doc_id}/{safe_name}"
    try:
        sb.storage.from_(settings.storage_bucket).upload(storage_path, content)
    except Exception as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Storage upload failed") from exc

    doc_res = (
        sb.table("documents")
        .insert(
            {
                "id": doc_id,
                "org_id": membership["org_id"],
                "title": title,
                "doc_type": doc_type,
                "content": text,
                "storage_path": storage_path,
                "created_by": user_id,
            }
        )
        .execute()
    )
    job_res = (
        sb.table("ingestion_jobs")
        .insert({"org_id": membership["org_id"], "document_id": doc_id, "status": "queued", "created_by": user_id})
        .execute()
    )
    job = (job_res.data or [None])[0]
    if job:
        process_ingestion_job.delay(job["id"])
    write_audit(membership["org_id"], user_id, "document.uploaded", "document", doc_id)
    return {"document": (doc_res.data or [None])[0], "job": job}


@router.post("/paste")
def paste_document(body: PasteBody, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    require_role(membership, "analyst")
    check_rate_limit(user_id, get_settings().rate_limit_per_minute, scope="paste")
    settings = get_settings()
    if len(body.content.encode("utf-8")) > settings.max_upload_bytes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Content exceeds max size")
    if _document_quota_exceeded(membership["org_id"]):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Document quota exceeded")

    sb = get_supabase_admin()
    text = redact_pii(sanitize_user_content(body.content))
    doc_id = str(uuid.uuid4())
    doc_res = (
        sb.table("documents")
        .insert(
            {
                "id": doc_id,
                "org_id": membership["org_id"],
                "title": body.title,
                "doc_type": body.doc_type,
                "content": text,
                "created_by": user_id,
            }
        )
        .execute()
    )
    job_res = (
        sb.table("ingestion_jobs")
        .insert({"org_id": membership["org_id"], "document_id": doc_id, "status": "queued", "created_by": user_id})
        .execute()
    )
    job = (job_res.data or [None])[0]
    if job:
        process_ingestion_job.delay(job["id"])
    write_audit(membership["org_id"], user_id, "document.pasted", "document", doc_id)
    return {"document": (doc_res.data or [None])[0], "job": job}


@router.get("/jobs/{job_id}")
def get_job(job_id: str, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    sb = get_supabase_admin()
    res = (
        sb.table("ingestion_jobs")
        .select("id, org_id, document_id, status, created_at, updated_at")
        .eq("id", job_id)
        .eq("org_id", membership["org_id"])
        .limit(1)
        .execute()
    )
    job = (res.data or [None])[0]
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    if job.get("status") == "failed":
        job = {**job, "error": "Processing failed"}
    return {"job": job}
