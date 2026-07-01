"""
File: services/api/app/routers/enrichment.py
Layer: FastAPI Route Layer
Purpose: Enrichment job status for org admins.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.deps.org_scope import require_onboarded_scope
from app.services.org_context import OrgScope, require_permission
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.security.client_errors import client_safe_error_message

router = APIRouter(prefix="/v1/enrichment", tags=["enrichment"])


def _sanitize_job_row(row: dict) -> dict:
    safe = dict(row)
    if safe.get("error"):
        safe["error"] = client_safe_error_message(str(safe["error"]), context="enrichment")
    return safe


@router.get("/jobs")
def list_enrichment_jobs(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "documents:read")
    sb = get_supabase_admin()
    res = (
        sb.table("enrichment_jobs")
        .select(
            "id, job_type, status, target_type, target_id, result_summary, error, created_at, completed_at"
        )
        .eq("org_id", scope.org_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return {"jobs": [_sanitize_job_row(row) for row in (res.data or [])]}
