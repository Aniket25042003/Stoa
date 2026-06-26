"""Enrichment job persistence helpers."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from stoa_core.config import get_settings
from stoa_core.db.supabase import get_supabase_admin

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def count_org_jobs_today(org_id: str) -> int:
    sb = get_supabase_admin()
    today = datetime.now(UTC).date().isoformat()
    res = (
        sb.table("enrichment_jobs")
        .select("id", count="exact")
        .eq("org_id", org_id)
        .gte("created_at", f"{today}T00:00:00+00:00")
        .execute()
    )
    return res.count or 0


def can_enqueue_org_job(org_id: str) -> bool:
    settings = get_settings()
    return count_org_jobs_today(org_id) < settings.enrichment_max_jobs_per_org_per_day


def find_job_by_idempotency(org_id: str, idempotency_key: str) -> dict[str, Any] | None:
    sb = get_supabase_admin()
    res = (
        sb.table("enrichment_jobs")
        .select("*")
        .eq("org_id", org_id)
        .eq("idempotency_key", idempotency_key)
        .in_("status", ["queued", "running"])
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return (res.data or [None])[0]


def create_enrichment_job(
    org_id: str,
    *,
    job_type: str,
    idempotency_key: str | None = None,
    target_type: str | None = None,
    target_id: str | None = None,
    payload: dict[str, Any] | None = None,
    created_by: str | None = None,
) -> dict[str, Any] | None:
    if not can_enqueue_org_job(org_id):
        logger.warning("Enrichment daily cap reached for org=%s", org_id)
        return None

    if idempotency_key:
        existing = find_job_by_idempotency(org_id, idempotency_key)
        if existing:
            return existing

    sb = get_supabase_admin()
    row = {
        "id": str(uuid.uuid4()),
        "org_id": org_id,
        "job_type": job_type,
        "status": "queued",
        "target_type": target_type,
        "target_id": target_id,
        "payload": payload or {},
        "idempotency_key": idempotency_key,
        "created_by": created_by,
    }
    res = sb.table("enrichment_jobs").insert(row).execute()
    return (res.data or [row])[0]


def mark_job_running(job_id: str) -> None:
    sb = get_supabase_admin()
    sb.table("enrichment_jobs").update(
        {"status": "running", "updated_at": _utc_now()}
    ).eq("id", job_id).execute()


def mark_job_completed(job_id: str, result_summary: dict[str, Any] | None = None) -> None:
    sb = get_supabase_admin()
    sb.table("enrichment_jobs").update(
        {
            "status": "completed",
            "result_summary": result_summary or {},
            "completed_at": _utc_now(),
            "updated_at": _utc_now(),
        }
    ).eq("id", job_id).execute()


def mark_job_failed(job_id: str, error: str) -> None:
    sb = get_supabase_admin()
    sb.table("enrichment_jobs").update(
        {
            "status": "failed",
            "error": error[:2000],
            "completed_at": _utc_now(),
            "updated_at": _utc_now(),
        }
    ).eq("id", job_id).execute()


def cleanup_stale_jobs(*, stale_hours: int = 1) -> int:
    from datetime import timedelta

    sb = get_supabase_admin()
    cutoff = datetime.now(UTC) - timedelta(hours=stale_hours)
    res = (
        sb.table("enrichment_jobs")
        .select("id, updated_at")
        .eq("status", "running")
        .execute()
    )
    updated = 0
    for row in res.data or []:
        updated_at = row.get("updated_at")
        if not updated_at:
            continue
        try:
            ts = datetime.fromisoformat(str(updated_at).replace("Z", "+00:00"))
        except ValueError:
            continue
        if ts > cutoff:
            continue
        sb.table("enrichment_jobs").update(
            {
                "status": "failed",
                "error": "Job timed out",
                "completed_at": datetime.now(UTC).isoformat(),
            }
        ).eq("id", row["id"]).eq("status", "running").execute()
        updated += 1
    return updated


def pending_jobs_for_org(org_id: str) -> int:
    sb = get_supabase_admin()
    res = (
        sb.table("enrichment_jobs")
        .select("id", count="exact")
        .eq("org_id", org_id)
        .in_("status", ["queued", "running"])
        .execute()
    )
    return res.count or 0
