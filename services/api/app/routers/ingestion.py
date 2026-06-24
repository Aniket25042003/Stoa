"""
File: services/api/app/routers/ingestion.py
Layer: FastAPI Route Layer
Purpose: Exposes authenticated REST endpoints and coordinates validation, permissions, and service calls.
Dependencies: FastAPI, Supabase, Pydantic, stoa_core
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.deps.org_scope import require_onboarded_scope
from app.deps.rate_limit import check_rate_limit
from app.services.document_ingestion import document_quota_exceeded, queue_text_document, queue_uploaded_document
from app.services.audit import write_audit
from app.services.org_context import OrgScope, require_permission
from stoa_core.config import get_settings
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.security.pii import redact_pii
from stoa_core.security.sanitize import (
    UploadValidationError,
    sanitize_user_content,
    validate_doc_type,
    validate_upload,
)

router = APIRouter(prefix="/v1/ingestion", tags=["ingestion"])


class PasteBody(BaseModel):
    """Manage PasteBody behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=1, max_length=10 * 1024 * 1024)
    doc_type: str = Field(default="note", pattern="^(call_transcript|review|crm_export|note)$")


def _document_quota_exceeded(org_id: str) -> bool:
    """Handles  document quota exceeded logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.

    Returns:
        bool: Result produced for the caller.
    """
    return document_quota_exceeded(org_id)


@router.get("/sources")
def list_sources(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    """Handles list sources logic for the surrounding Stoa workflow.

    Args:
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "data_sources:read")
    sb = get_supabase_admin()
    res = (
        sb.table("data_sources")
        .select("id, org_id, label, source_type, status, created_at")
        .eq("org_id", scope.org_id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"sources": res.data or []}


@router.post("/upload")
async def upload_document(
    title: str = Form(..., min_length=1, max_length=300),
    doc_type: str = Form("note"),
    file: UploadFile = File(...),
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, Any]:
    """Asynchronously handles upload document logic for the surrounding Stoa workflow.

    Args:
        title (str): Input value used by this workflow step.
        doc_type (str): Input value used by this workflow step.
        file (UploadFile): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "documents:write")
    check_rate_limit(scope.user_id, get_settings().rate_limit_per_minute, scope="upload")
    settings = get_settings()

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
        validate_upload(
            file.filename or "upload.txt",
            file.content_type,
            len(content),
            settings.max_upload_bytes,
            content=content,
        )
    except UploadValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    text = redact_pii(sanitize_user_content(content.decode("utf-8", errors="replace")))

    if _document_quota_exceeded(scope.org_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Document quota exceeded")

    try:
        doc, job = queue_uploaded_document(
            org_id=scope.org_id,
            user_id=scope.user_id,
            title=title,
            doc_type=doc_type,
            filename=file.filename or "upload.txt",
            raw_bytes=content,
            text=text,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Storage upload failed") from exc

    write_audit(scope.org_id, scope.user_id, "document.uploaded", "document", doc["id"] if doc else "")
    return {"document": doc, "job": job}


@router.post("/paste")
def paste_document(body: PasteBody, scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    """Handles paste document logic for the surrounding Stoa workflow.

    Args:
        body (PasteBody): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "documents:write")
    check_rate_limit(scope.user_id, get_settings().rate_limit_per_minute, scope="paste")
    settings = get_settings()
    if len(body.content.encode("utf-8")) > settings.max_upload_bytes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Content exceeds max size")
    if _document_quota_exceeded(scope.org_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Document quota exceeded")

    try:
        doc, job = queue_text_document(
            org_id=scope.org_id,
            user_id=scope.user_id,
            title=body.title,
            content=body.content,
            doc_type=body.doc_type,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    write_audit(scope.org_id, scope.user_id, "document.pasted", "document", doc["id"] if doc else "")
    return {"document": doc, "job": job}


@router.get("/jobs/{job_id}")
def get_job(job_id: str, scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    """Handles get job logic for the surrounding Stoa workflow.

    Args:
        job_id (str): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "documents:read")
    sb = get_supabase_admin()
    res = (
        sb.table("ingestion_jobs")
        .select("id, org_id, document_id, status, created_at, finished_at")
        .eq("id", job_id)
        .eq("org_id", scope.org_id)
        .limit(1)
        .execute()
    )
    job = (res.data or [None])[0]
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    if job.get("status") == "failed":
        job = {**job, "error": "Processing failed"}
    return {"job": job}
