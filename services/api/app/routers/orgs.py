"""
File: services/api/app/routers/orgs.py
Layer: FastAPI Route Layer
Purpose: Exposes authenticated REST endpoints and coordinates validation, permissions, and service calls.
Dependencies: FastAPI, Supabase, Pydantic, stoa_core
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.deps.auth import verify_supabase_jwt, verify_supabase_jwt_payload
from app.deps.org_scope import require_onboarded_scope
from app.tasks.enrichment import enrich_company
from app.services.auth_state import email_from_claims, filter_memberships_for_display
from app.services.org_context import (
    OrgScope,
    count_org_owners,
    list_user_memberships,
    require_owner,
    require_permission,
    set_last_active_org,
)
from app.services.org_summary import build_completeness_for_org
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.rag.ingest import ingest_knowledge, profile_to_knowledge_text
from stoa_core.security.permissions import SYSTEM_ROLE_ADMIN, SYSTEM_ROLE_OWNER

router = APIRouter(prefix="/v1/orgs", tags=["organizations"])


class OrgProfileUpdate(BaseModel):
    """Manage OrgProfileUpdate behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    target_customers: str | None = None
    business_model: str | None = None
    stage: str | None = None
    goals: str | None = None
    brand_voice: str | None = None
    known_competitors_notes: str | None = None
    company_size: str | None = None
    market: str | None = None


class OrgUpdate(BaseModel):
    """Manage OrgUpdate behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    name: str | None = None
    website_url: str | None = None
    industry: str | None = None
    profile: OrgProfileUpdate | None = None


class OrgSwitchBody(BaseModel):
    """Manage OrgSwitchBody behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    org_id: str


class TransferOwnershipBody(BaseModel):
    """Manage TransferOwnershipBody behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    target_user_id: str


class OrgDeleteBody(BaseModel):
    """Manage OrgDeleteBody behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    confirm_name: str


def _merge_profile(existing: dict[str, Any], update: OrgProfileUpdate | None) -> dict[str, Any]:
    """Handles  merge profile logic for the surrounding Stoa workflow.

    Args:
        existing (dict[str, Any]): Input value used by this workflow step.
        update (OrgProfileUpdate | None): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    merged = dict(existing or {})
    if update is None:
        return merged
    for key, value in update.model_dump(exclude_none=True).items():
        merged[key] = value
    return merged


@router.get("")
def list_orgs(claims: dict = Depends(verify_supabase_jwt_payload)) -> dict[str, Any]:
    """Handles list orgs logic for the surrounding Stoa workflow.

    Args:
        claims (dict): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    user_id = str(claims["sub"])
    email = email_from_claims(claims)
    sb = get_supabase_admin()
    profile_row = (
        sb.table("user_profiles")
        .select("last_active_org_id, full_name")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    profile = (profile_row.data or [{}])[0]
    active_org_id = profile.get("last_active_org_id")
    full_name = profile.get("full_name")
    memberships = filter_memberships_for_display(
        list_user_memberships(user_id),
        full_name=full_name,
        email=email,
    )
    visible_org_ids = {m["org_id"] for m in memberships}
    if active_org_id and active_org_id not in visible_org_ids:
        active_org_id = memberships[0]["org_id"] if memberships else None
        if active_org_id:
            set_last_active_org(user_id, str(active_org_id))
    return {
        "active_org_id": str(active_org_id) if active_org_id else None,
        "organizations": [
            {
                "org_id": m["org_id"],
                "role": m.get("role"),
                "role_id": m.get("role_id"),
                "role_name": (m.get("org_roles") or {}).get("name"),
                "role_key": (m.get("org_roles") or {}).get("role_key"),
                "org": m.get("organizations"),
            }
            for m in memberships
        ],
    }


@router.post("/switch")
def switch_org(body: OrgSwitchBody, user_id: str = Depends(verify_supabase_jwt)) -> dict[str, Any]:
    """Handles switch org logic for the surrounding Stoa workflow.

    Args:
        body (OrgSwitchBody): Input value used by this workflow step.
        user_id (str): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    from app.services.org_context import _load_membership

    membership = _load_membership(user_id, body.org_id)
    if not membership:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Organization access denied")
    set_last_active_org(user_id, body.org_id)
    return {
        "active_org_id": body.org_id,
        "membership": {
            "id": membership["id"],
            "org_id": membership["org_id"],
            "role_name": (membership.get("org_roles") or {}).get("name"),
        },
    }


@router.get("/me")
def get_my_org(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    """Handles get my org logic for the surrounding Stoa workflow.

    Args:
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    org = scope.org
    completeness = build_completeness_for_org(org)
    return {
        "org": org,
        "membership": {
            "id": scope.membership["id"],
            "role": scope.membership.get("role"),
            "role_id": scope.membership.get("role_id"),
            "role_name": scope.role_name,
            "role_key": scope.role_key,
            "org_id": scope.org_id,
            "permissions": sorted(scope.permissions),
        },
        "completeness": completeness,
    }


@router.post("/leave")
def leave_org(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, str]:
    """Handles leave org logic for the surrounding Stoa workflow.

    Args:
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, str]: Result produced for the caller.
    """
    require_permission(scope, "org:leave")
    if scope.is_owner and count_org_owners(scope.org_id) <= 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Transfer ownership before leaving as the last owner")
    sb = get_supabase_admin()
    sb.table("memberships").delete().eq("id", scope.membership["id"]).execute()
    write_audit(scope.org_id, scope.user_id, "member.left", "membership", scope.membership["id"])
    profile = sb.table("user_profiles").select("last_active_org_id").eq("user_id", scope.user_id).limit(1).execute()
    if (profile.data or [{}])[0].get("last_active_org_id") == scope.org_id:
        remaining = list_user_memberships(scope.user_id)
        next_org = remaining[0]["org_id"] if remaining else None
        sb.table("user_profiles").update({"last_active_org_id": next_org}).eq("user_id", scope.user_id).execute()
    return {"status": "left"}


@router.post("/transfer-ownership")
def transfer_ownership(body: TransferOwnershipBody, scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, str]:
    """Handles transfer ownership logic for the surrounding Stoa workflow.

    Args:
        body (TransferOwnershipBody): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, str]: Result produced for the caller.
    """
    require_owner(scope)
    sb = get_supabase_admin()
    target = (
        sb.table("memberships")
        .select("id, user_id, role_id, org_roles(role_key)")
        .eq("org_id", scope.org_id)
        .eq("user_id", body.target_user_id)
        .limit(1)
        .execute()
    )
    target_membership = (target.data or [None])[0]
    if not target_membership:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Target user is not a member of this organization")
    owner_role = (
        sb.table("org_roles").select("id").eq("org_id", scope.org_id).eq("role_key", SYSTEM_ROLE_OWNER).limit(1).execute()
    )
    admin_role = (
        sb.table("org_roles").select("id").eq("org_id", scope.org_id).eq("role_key", SYSTEM_ROLE_ADMIN).limit(1).execute()
    )
    owner_role_id = (owner_role.data or [{}])[0].get("id")
    admin_role_id = (admin_role.data or [{}])[0].get("id")
    if not owner_role_id or not admin_role_id:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "System roles missing")
    sb.table("memberships").update({"role_id": owner_role_id, "role": SYSTEM_ROLE_OWNER}).eq("id", target_membership["id"]).execute()
    sb.table("memberships").update({"role_id": admin_role_id, "role": SYSTEM_ROLE_ADMIN}).eq("id", scope.membership["id"]).execute()
    write_audit(scope.org_id, scope.user_id, "org.ownership_transferred", "organization", scope.org_id, {"to": body.target_user_id})
    return {"status": "transferred"}


@router.delete("/me")
def delete_org(body: OrgDeleteBody, scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, str]:
    """Handles delete org logic for the surrounding Stoa workflow.

    Args:
        body (OrgDeleteBody): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, str]: Result produced for the caller.
    """
    require_owner(scope)
    org_name = scope.org.get("name") or ""
    if body.confirm_name.strip() != org_name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Organization name confirmation does not match")
    sb = get_supabase_admin()
    sb.table("organizations").delete().eq("id", scope.org_id).execute()
    write_audit(scope.org_id, scope.user_id, "org.deleted", "organization", scope.org_id)
    remaining = list_user_memberships(scope.user_id)
    next_org = remaining[0]["org_id"] if remaining else None
    sb.table("user_profiles").update({"last_active_org_id": next_org}).eq("user_id", scope.user_id).execute()
    return {"status": "deleted"}


@router.patch("/me")
def update_my_org(body: OrgUpdate, scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    """Handles update my org logic for the surrounding Stoa workflow.

    Args:
        body (OrgUpdate): Input value used by this workflow step.
        scope (OrgScope): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    require_permission(scope, "org:update")
    sb = get_supabase_admin()
    org_id = scope.org_id
    current = scope.org
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
        write_audit(org_id, scope.user_id, "org.updated", "organization", org_id, updates)
        updated_org = org or current
        ingest_knowledge(
            org_id,
            kind="company_profile",
            title=f"{updated_org.get('name', 'Company')} profile",
            text=profile_to_knowledge_text(updated_org),
            feature_origin="data",
            uri=f"org:{org_id}:company_profile",
        )
        if any(k in updates for k in ("website_url", "industry", "name", "profile")):
            suffix = str(hash(frozenset(updates.items())))[-8:]
            enrich_company.delay(org_id, user_id=scope.user_id, idempotency_suffix=f"patch:{suffix}")
    completeness = build_completeness_for_org(org or current)
    return {"org": org or current, "completeness": completeness}


# Legacy alias — prefer POST /v1/onboarding/complete
@router.post("/onboarding")
def legacy_complete_onboarding() -> dict[str, str]:
    """Handles legacy complete onboarding logic for the surrounding Stoa workflow.

    Returns:
        dict[str, str]: Result produced for the caller.
    """
    raise HTTPException(
        status.HTTP_410_GONE,
        "Use POST /v1/onboarding/complete instead.",
    )
