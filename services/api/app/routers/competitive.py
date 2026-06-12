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
    name: str = Field(min_length=1, max_length=200)
    website_url: HttpUrl | None = None
    pricing_url: HttpUrl | None = None


@router.get("/competitors")
def list_competitors(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
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
    require_permission(scope, "competitive:manage")
    check_rate_limit(scope.user_id, limit_per_minute=10, scope="competitor_add")
    website_url = str(body.website_url) if body.website_url else None
    pricing_url = str(body.pricing_url) if body.pricing_url else None
    for url in (website_url, pricing_url):
        if url:
            try:
                assert_safe_fetch_url(url)
            except ValueError as exc:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
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


@router.get("/alerts")
def list_alerts(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
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
