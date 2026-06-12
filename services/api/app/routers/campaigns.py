from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.deps.org_scope import require_onboarded_scope
from app.deps.rate_limit import check_rate_limit
from app.services.audit import write_audit
from app.services.org_context import OrgScope, require_permission
from app.tasks.campaigns import generate_campaign
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.security.sanitize import sanitize_user_content

router = APIRouter(prefix="/v1/campaigns", tags=["campaigns"])


class CampaignCreate(BaseModel):
    brief: str = Field(min_length=10, max_length=5000)
    brand_voice: str | None = None


@router.get("")
def list_campaigns(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "campaigns:read")
    sb = get_supabase_admin()
    res = (
        sb.table("campaigns")
        .select("id, org_id, brief, brand_voice, status, created_at, updated_at")
        .eq("org_id", scope.org_id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"campaigns": res.data or []}


@router.post("")
def create_campaign(body: CampaignCreate, scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "campaigns:create")
    check_rate_limit(scope.user_id, limit_per_minute=10, scope="campaign_create")
    sb = get_supabase_admin()
    brief = sanitize_user_content(body.brief)
    res = (
        sb.table("campaigns")
        .insert(
            {
                "org_id": scope.org_id,
                "brief": brief,
                "brand_voice": body.brand_voice,
                "status": "queued",
                "created_by": scope.user_id,
            }
        )
        .execute()
    )
    campaign = (res.data or [None])[0]
    if campaign:
        generate_campaign.delay(campaign["id"])
        write_audit(scope.org_id, scope.user_id, "campaign.created", "campaign", campaign["id"])
    return {"campaign": campaign}


@router.get("/{campaign_id}")
def get_campaign(campaign_id: str, scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "campaigns:read")
    sb = get_supabase_admin()
    res = (
        sb.table("campaigns")
        .select("id, org_id, brief, brand_voice, status, assets, error, created_at, updated_at")
        .eq("id", campaign_id)
        .eq("org_id", scope.org_id)
        .limit(1)
        .execute()
    )
    if not res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found")
    return {"campaign": res.data[0]}
