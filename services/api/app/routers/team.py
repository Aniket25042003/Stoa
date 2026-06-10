from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.deps.auth import verify_supabase_jwt_payload, verify_supabase_jwt_payload_verified
from app.services.audit import write_audit
from app.services.auth_state import email_from_claims, get_or_create_user_profile
from app.services.org_context import get_user_membership, require_role
from stoa_core.config import get_settings
from stoa_core.db.supabase import get_supabase_admin

router = APIRouter(prefix="/v1/team", tags=["team"])


class InviteCreate(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    role: str = Field(pattern="^(admin|analyst|viewer)$")


class InviteAccept(BaseModel):
    token: str = Field(min_length=16)


def _invite_pepper() -> str:
    settings = get_settings()
    pepper = settings.invite_token_pepper.strip()
    if pepper:
        return pepper
    if settings.is_production:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Invite configuration error")
    return "dev-only-insecure-pepper"


def _hash_token(token: str) -> str:
    return hashlib.sha256(f"{token}.{_invite_pepper()}".encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def current_user_id(claims: dict[str, Any] = Depends(verify_supabase_jwt_payload_verified)) -> str:
    return str(claims["sub"])


def _send_supabase_invite(email: str, invite_url: str) -> None:
    """Use Supabase Auth invite emails; delivery goes through configured Brevo SMTP."""
    sb = get_supabase_admin()
    try:
        # supabase-py exposes this in recent versions. Keep best-effort so local
        # dev/tests still get the returned invite_url even if admin email is unavailable.
        sb.auth.admin.invite_user_by_email(email, {"redirect_to": invite_url})
    except Exception:
        return


def _org_is_empty_placeholder(org_id: str) -> bool:
    sb = get_supabase_admin()
    documents = sb.table("documents").select("id", count="exact").eq("org_id", org_id).execute().count or 0
    campaigns = sb.table("campaigns").select("id", count="exact").eq("org_id", org_id).execute().count or 0
    knowledge = sb.table("knowledge_items").select("id", count="exact").eq("org_id", org_id).execute().count or 0
    org_res = sb.table("organizations").select("onboarding_completed_at").eq("id", org_id).limit(1).execute()
    org = (org_res.data or [{}])[0]
    return documents == 0 and campaigns == 0 and knowledge == 0 and not org.get("onboarding_completed_at")


@router.get("/members")
def list_members(user_id: str = Depends(current_user_id)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    require_role(membership, "admin")
    sb = get_supabase_admin()
    members_res = (
        sb.table("memberships")
        .select("id, user_id, role, created_at")
        .eq("org_id", membership["org_id"])
        .order("created_at", desc=False)
        .execute()
    )
    members = members_res.data or []
    user_ids = [m["user_id"] for m in members]
    profiles: dict[str, dict[str, Any]] = {}
    if user_ids:
        profiles_res = sb.table("user_profiles").select("*").in_("user_id", user_ids).execute()
        profiles = {p["user_id"]: p for p in profiles_res.data or []}
    return {
        "members": [
            {
                **m,
                "profile": profiles.get(m["user_id"], {}),
            }
            for m in members
        ]
    }


@router.get("/invites")
def list_invites(user_id: str = Depends(current_user_id)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    require_role(membership, "admin")
    sb = get_supabase_admin()
    res = (
        sb.table("org_invites")
        .select("id, email, role, expires_at, accepted_at, revoked_at, created_at")
        .eq("org_id", membership["org_id"])
        .order("created_at", desc=True)
        .execute()
    )
    return {"invites": res.data or []}


@router.post("/invites")
def create_invite(body: InviteCreate, claims: dict[str, Any] = Depends(verify_supabase_jwt_payload_verified)) -> dict[str, Any]:
    user_id = str(claims["sub"])
    membership = get_user_membership(user_id)
    require_role(membership, "admin")

    email = body.email.lower()
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    expires_at = (_now() + timedelta(days=7)).isoformat()
    sb = get_supabase_admin()

    res = (
        sb.table("org_invites")
        .insert(
            {
                "org_id": membership["org_id"],
                "email": email,
                "role": body.role,
                "token_hash": token_hash,
                "invited_by": user_id,
                "expires_at": expires_at,
            }
        )
        .execute()
    )
    invite = (res.data or [None])[0]
    if not invite:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to create invite")

    settings = get_settings()
    invite_url = f"{settings.app_base_url.rstrip('/')}/invite/{token}"
    _send_supabase_invite(email, invite_url)
    write_audit(membership["org_id"], user_id, "member.invited", "org_invite", invite["id"], {"email": email, "role": body.role})
    response: dict[str, Any] = {"invite": {k: v for k, v in invite.items() if k != "token_hash"}}
    if not settings.is_production:
        response["invite_url"] = invite_url
    return response


@router.post("/invites/{invite_id}/revoke")
def revoke_invite(invite_id: str, user_id: str = Depends(current_user_id)) -> dict[str, Any]:
    membership = get_user_membership(user_id)
    require_role(membership, "admin")
    sb = get_supabase_admin()
    res = (
        sb.table("org_invites")
        .update({"revoked_at": _now().isoformat()})
        .eq("id", invite_id)
        .eq("org_id", membership["org_id"])
        .execute()
    )
    invite = (res.data or [None])[0]
    if not invite:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite not found")
    write_audit(membership["org_id"], user_id, "member.invite_revoked", "org_invite", invite_id)
    return {"invite": {k: v for k, v in invite.items() if k != "token_hash"}}


@router.post("/invites/accept")
def accept_invite(body: InviteAccept, claims: dict[str, Any] = Depends(verify_supabase_jwt_payload)) -> dict[str, Any]:
    user_id = str(claims["sub"])
    get_or_create_user_profile(user_id, claims)
    email = email_from_claims(claims)
    token_hash = _hash_token(body.token)
    sb = get_supabase_admin()
    invite_res = (
        sb.table("org_invites")
        .select("*")
        .eq("token_hash", token_hash)
        .is_("accepted_at", "null")
        .is_("revoked_at", "null")
        .limit(1)
        .execute()
    )
    invite = (invite_res.data or [None])[0]
    if not invite:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite not found or already used")
    if datetime.fromisoformat(invite["expires_at"].replace("Z", "+00:00")) < _now():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invite expired")
    if invite["email"].lower() != email:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sign in with the invited email address")

    membership_res = sb.table("memberships").select("*").eq("user_id", user_id).limit(1).execute()
    existing = (membership_res.data or [None])[0]
    if existing and existing["org_id"] != invite["org_id"]:
        if not _org_is_empty_placeholder(existing["org_id"]):
            raise HTTPException(status.HTTP_409_CONFLICT, "This account already belongs to another company")
        sb.table("memberships").update({"org_id": invite["org_id"], "role": invite["role"]}).eq("id", existing["id"]).execute()
        sb.table("organizations").delete().eq("id", existing["org_id"]).execute()
    elif existing and existing["org_id"] == invite["org_id"]:
        sb.table("memberships").update({"role": invite["role"]}).eq("id", existing["id"]).execute()
    else:
        sb.table("memberships").insert({"org_id": invite["org_id"], "user_id": user_id, "role": invite["role"]}).execute()

    accepted_at = _now().isoformat()
    sb.table("org_invites").update({"accepted_by": user_id, "accepted_at": accepted_at}).eq("id", invite["id"]).execute()
    write_audit(invite["org_id"], user_id, "member.joined", "org_invite", invite["id"], {"email": email, "role": invite["role"]})
    return {"accepted": True, "org_id": invite["org_id"], "role": invite["role"]}
