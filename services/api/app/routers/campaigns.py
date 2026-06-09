from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.deps.auth import verify_supabase_jwt
from app.deps.rate_limit import check_rate_limit
from stoa_core.security.sanitize import sanitize_user_content
from app.services.audit import write_audit
from app.services.org_context import get_user_membership, require_role
from app.tasks.campaigns import generate_campaign
from stoa_core.db.supabase import get_supabase_admin

router = APIRouter(prefix="/v1/campaigns", tags=["campaigns"])


class CampaignCreate(BaseModel):
    brief: str = Field(min_length=10, max_length=5000)
    brand_voice: str | None = None


@router.get("")
def list_campaigns(user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    sb = get_supabase_admin()
    res = (
        sb.table("campaigns")
        .select("id, org_id, brief, brand_voice, status, created_at, updated_at")
        .eq("org_id", membership["org_id"])
        .order("created_at", desc=True)
        .execute()
    )
    return {"campaigns": res.data or []}


@router.post("")
def create_campaign(body: CampaignCreate, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    require_role(membership, "analyst")
    check_rate_limit(user_id, limit_per_minute=10, scope="campaign_create")
    sb = get_supabase_admin()
    brief = sanitize_user_content(body.brief)
    res = (
        sb.table("campaigns")
        .insert(
            {
                "org_id": membership["org_id"],
                "brief": brief,
                "brand_voice": body.brand_voice,
                "status": "queued",
                "created_by": user_id,
            }
        )
        .execute()
    )
    campaign = (res.data or [None])[0]
    if campaign:
        generate_campaign.delay(campaign["id"])
        write_audit(membership["org_id"], user_id, "campaign.created", "campaign", campaign["id"])
    return {"campaign": campaign}


@router.get("/{campaign_id}")
def get_campaign(campaign_id: str, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    sb = get_supabase_admin()
    res = (
        sb.table("campaigns")
        .select("id, org_id, brief, brand_voice, status, output, created_at, updated_at")
        .eq("id", campaign_id)
        .eq("org_id", membership["org_id"])
        .limit(1)
        .execute()
    )
    if not res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Campaign not found")
    return {"campaign": res.data[0]}
