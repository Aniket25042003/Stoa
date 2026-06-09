from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.deps.auth import verify_supabase_jwt
from app.services.audit import write_audit
from app.services.org_summary import build_completeness_for_org
from app.services.org_context import get_user_membership, require_role
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.rag.ingest import ingest_knowledge, profile_to_knowledge_text

router = APIRouter(prefix="/v1/orgs", tags=["organizations"])


class OrgProfileUpdate(BaseModel):
    target_customers: str | None = None
    business_model: str | None = None
    stage: str | None = None
    goals: str | None = None
    brand_voice: str | None = None
    known_competitors_notes: str | None = None
    company_size: str | None = None
    market: str | None = None


class OrgUpdate(BaseModel):
    name: str | None = None
    website_url: str | None = None
    industry: str | None = None
    profile: OrgProfileUpdate | None = None


class OnboardingBody(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    website_url: str | None = None
    industry: str | None = None
    role_type: str | None = None
    job_title: str | None = None
    use_case: str | None = None
    profile: OrgProfileUpdate | None = None
    complete: bool = False


def _merge_profile(existing: dict[str, Any], update: OrgProfileUpdate | None) -> dict[str, Any]:
    merged = dict(existing or {})
    if update is None:
        return merged
    for key, value in update.model_dump(exclude_none=True).items():
        merged[key] = value
    return merged


@router.get("/me")
def get_my_org(user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    org = membership.get("organizations") or {}
    completeness = build_completeness_for_org(org)
    return {
        "org": org,
        "membership": {"id": membership["id"], "role": membership["role"], "org_id": membership["org_id"]},
        "completeness": completeness,
    }


@router.post("/onboarding")
def complete_onboarding(body: OnboardingBody, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    sb = get_supabase_admin()
    from app.services.auth_state import utc_now_iso

    completed_at = utc_now_iso() if body.complete else None
    profile_payload = body.profile.model_dump(exclude_none=True) if body.profile else {}
    user_profile_updates = {
        k: v
        for k, v in {
            "role_type": body.role_type,
            "job_title": body.job_title,
            "use_case": body.use_case,
            "onboarding_completed_at": completed_at,
        }.items()
        if v is not None
    }
    if user_profile_updates:
        sb.table("user_profiles").update(user_profile_updates).eq("user_id", user_id).execute()

    existing = (
        sb.table("memberships")
        .select("id, org_id, role, organizations(id, name, slug, website_url, industry, profile, onboarding_completed_at)")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if existing.data:
        membership = existing.data[0]
        org_id = membership["org_id"]
        updates = {
            "name": body.name,
            "website_url": body.website_url,
            "industry": body.industry,
        }
        current_profile = ((membership.get("organizations") or {}).get("profile") or {}) if membership else {}
        if profile_payload:
            updates["profile"] = {**current_profile, **profile_payload}
        if completed_at:
            updates["onboarding_completed_at"] = completed_at
        res = sb.table("organizations").update(updates).eq("id", org_id).execute()
        org = (res.data or [None])[0] or membership.get("organizations") or {}
        write_audit(org_id, user_id, "org.onboarding_updated", "organization", org_id, updates)
        if completed_at:
            write_audit(org_id, user_id, "onboarding.completed", "organization", org_id)
        ingest_knowledge(
            org_id,
            kind="company_profile",
            title=f"{org.get('name', 'Company')} profile",
            text=profile_to_knowledge_text(org),
            feature_origin="onboarding",
            uri=f"org_profile:{org_id}",
        )
        completeness = build_completeness_for_org(org)
        return {"org": org, "completeness": completeness}

    slug = body.name.lower().replace(" ", "-")[:80]
    org_res = (
        sb.table("organizations")
        .insert(
            {
                "name": body.name,
                "slug": slug,
                "website_url": body.website_url,
                "industry": body.industry,
                "profile": profile_payload,
                "onboarding_completed_at": completed_at,
            }
        )
        .execute()
    )
    org = (org_res.data or [None])[0]
    if not org:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to create organization")

    sb.table("memberships").insert({"org_id": org["id"], "user_id": user_id, "role": "owner"}).execute()
    write_audit(org["id"], user_id, "org.created", "organization", org["id"], {"name": body.name})
    if completed_at:
        write_audit(org["id"], user_id, "onboarding.completed", "organization", org["id"])
    ingest_knowledge(
        org["id"],
        kind="company_profile",
        title=f"{org.get('name', 'Company')} profile",
        text=profile_to_knowledge_text(org),
        feature_origin="onboarding",
        uri=f"org_profile:{org['id']}",
    )
    completeness = build_completeness_for_org(org)
    return {"org": org, "completeness": completeness}


@router.patch("/me")
def update_my_org(body: OrgUpdate, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    require_role(membership, "admin")
    sb = get_supabase_admin()
    org_id = membership["org_id"]
    current = membership.get("organizations") or {}

    scalar_updates = body.model_dump(exclude_none=True, exclude={"profile"})
    profile_updates = body.profile
    updates: dict[str, Any] = dict(scalar_updates)
    if profile_updates is not None:
        updates["profile"] = _merge_profile(current.get("profile") or {}, profile_updates)

    if not updates:
        org = current
    else:
        res = sb.table("organizations").update(updates).eq("id", org_id).execute()
        org = (res.data or [None])[0]
        write_audit(org_id, user_id, "org.updated", "organization", org_id, updates)

        updated_org = org or current
        ingest_knowledge(
            org_id,
            kind="company_profile",
            title=f"{updated_org.get('name', 'Company')} profile",
            text=profile_to_knowledge_text(updated_org),
            feature_origin="data",
            uri=f"org_profile:{org_id}",
        )

    completeness = build_completeness_for_org(org or current)
    return {"org": org or current, "completeness": completeness}
