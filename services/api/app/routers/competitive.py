"""
File: services/api/app/routers/competitive.py
Layer: FastAPI Route Layer
Purpose: Exposes authenticated REST endpoints and coordinates validation, permissions, and service calls.
Dependencies: FastAPI, Supabase, Pydantic, stoa_core
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl

from app.deps.org_scope import require_onboarded_scope
from app.deps.rate_limit import check_rate_limit
from app.services.audit import write_audit
from app.services.org_context import OrgScope, require_permission
from app.tasks.competitive import monitor_competitor
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.security.ssrf import assert_safe_fetch_url

router = APIRouter(prefix="/v1/competitive", tags=["competitive"])


class CompetitorCreate(BaseModel):
    """Manage CompetitorCreate behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    name: str = Field(min_length=1, max_length=200)
    website_url: HttpUrl | None = None
    pricing_url: HttpUrl | None = None


class CompetitorUpdate(BaseModel):
    """Manage CompetitorUpdate behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    name: str | None = Field(default=None, min_length=1, max_length=200)
    website_url: HttpUrl | None = None
    pricing_url: HttpUrl | None = None


def _get_competitor_for_org(org_id: str, competitor_id: str) -> dict[str, Any] | None:
    """Handles  get competitor for org logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.
        competitor_id (str): Input value used by this workflow step.

    Returns:
        dict[str, Any] | None: Result produced for the caller.
    """
    sb = get_supabase_admin()
    res = (
        sb.table("competitors")
        .select("id, org_id, name, website_url, pricing_url, last_scanned_at, created_at")
        .eq("id", competitor_id)
        .eq("org_id", org_id)
        .limit(1)
        .execute()
    )
    return (res.data or [None])[0]


def _validate_competitor_urls(*urls: str | None) -> None:
    """Handles  validate competitor urls logic for the surrounding Stoa workflow.
    """
    for url in urls:
        if url:
            try:
                assert_safe_fetch_url(url)
            except ValueError as exc:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.get("/competitors")
def list_competitors(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    """Handles list competitors logic for the surrounding Stoa workflow.

    Args:
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "competitive:read")
    sb = get_supabase_admin()
    res = (
        sb.table("competitors")
        .select("id, org_id, name, website_url, pricing_url, last_scanned_at, created_at")
        .eq("org_id", scope.org_id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"competitors": res.data or []}


@router.post("/competitors")
def add_competitor(body: CompetitorCreate, scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    """Handles add competitor logic for the surrounding Stoa workflow.

    Args:
        body (CompetitorCreate): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "competitive:manage")
    check_rate_limit(scope.user_id, limit_per_minute=10, scope="competitor_add")
    website_url = str(body.website_url) if body.website_url else None
    pricing_url = str(body.pricing_url) if body.pricing_url else None
    _validate_competitor_urls(website_url, pricing_url)
    sb = get_supabase_admin()
    res = (
        sb.table("competitors")
        .insert(
            {
                "org_id": scope.org_id,
                "name": body.name,
                "website_url": website_url,
                "pricing_url": pricing_url,
                "created_by": scope.user_id,
            }
        )
        .execute()
    )
    comp = (res.data or [None])[0]
    if comp:
        monitor_competitor.delay(comp["id"])
        write_audit(scope.org_id, scope.user_id, "competitor.added", "competitor", comp["id"])
    return {"competitor": comp}


@router.patch("/competitors/{competitor_id}")
def update_competitor(
    competitor_id: str,
    body: CompetitorUpdate,
    scope: OrgScope = Depends(require_onboarded_scope),
) -> dict[str, Any]:
    """Handles update competitor logic for the surrounding Stoa workflow.

    Args:
        competitor_id (str): Input value used by this workflow step.
        body (CompetitorUpdate): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "competitive:manage")
    check_rate_limit(scope.user_id, limit_per_minute=10, scope="competitor_update")
    existing = _get_competitor_for_org(scope.org_id, competitor_id)
    if not existing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Competitor not found")

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        return {"competitor": existing}

    if "website_url" in updates:
        updates["website_url"] = str(updates["website_url"]) if updates["website_url"] else None
    if "pricing_url" in updates:
        updates["pricing_url"] = str(updates["pricing_url"]) if updates["pricing_url"] else None

    _validate_competitor_urls(updates.get("website_url"), updates.get("pricing_url"))

    sb = get_supabase_admin()
    res = sb.table("competitors").update(updates).eq("id", competitor_id).eq("org_id", scope.org_id).execute()
    comp = (res.data or [None])[0]
    if not comp:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Competitor not found")

    url_changed = "website_url" in updates and updates["website_url"] != existing.get("website_url")
    pricing_changed = "pricing_url" in updates and updates["pricing_url"] != existing.get("pricing_url")
    if url_changed or pricing_changed:
        monitor_competitor.delay(competitor_id)

    write_audit(scope.org_id, scope.user_id, "competitor.updated", "competitor", competitor_id)
    return {"competitor": comp}


@router.delete("/competitors/{competitor_id}")
def delete_competitor(competitor_id: str, scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, str]:
    """Handles delete competitor logic for the surrounding Stoa workflow.

    Args:
        competitor_id (str): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, str]: Result produced for the caller.
    """
    require_permission(scope, "competitive:manage")
    check_rate_limit(scope.user_id, limit_per_minute=10, scope="competitor_delete")
    existing = _get_competitor_for_org(scope.org_id, competitor_id)
    if not existing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Competitor not found")

    sb = get_supabase_admin()
    sb.table("competitors").delete().eq("id", competitor_id).eq("org_id", scope.org_id).execute()
    write_audit(scope.org_id, scope.user_id, "competitor.deleted", "competitor", competitor_id)
    return {"status": "deleted"}


@router.get("/alerts")
def list_alerts(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    """Handles list alerts logic for the surrounding Stoa workflow.

    Args:
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "competitive:read")
    sb = get_supabase_admin()
    res = (
        sb.table("competitive_alerts")
        .select("*, competitors(name)")
        .eq("org_id", scope.org_id)
        .order("created_at", desc=True)
        .limit(100)
        .execute()
    )
    return {"alerts": res.data or []}


@router.post("/competitors/{competitor_id}/scan")
def trigger_scan(competitor_id: str, scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, str]:
    """Handles trigger scan logic for the surrounding Stoa workflow.

    Args:
        competitor_id (str): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, str]: Result produced for the caller.
    """
    require_permission(scope, "competitive:scan")
    check_rate_limit(scope.user_id, limit_per_minute=10, scope="competitor_scan")
    sb = get_supabase_admin()
    res = (
        sb.table("competitors")
        .select("id")
        .eq("id", competitor_id)
        .eq("org_id", scope.org_id)
        .limit(1)
        .execute()
    )
    if not res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Competitor not found")
    monitor_competitor.delay(competitor_id)
    return {"status": "queued"}
