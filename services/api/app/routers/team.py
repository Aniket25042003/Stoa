from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.deps.auth import verify_supabase_jwt_payload_verified
from app.deps.org_scope import require_onboarded_scope, verified_org_scope_dep
from app.services.audit import write_audit
from app.services.auth_state import email_from_claims, get_or_create_user_profile
from app.services.invites import hash_invite_token, invite_expires_at, new_invite_token
from app.services.org_context import OrgScope, assert_permission_boundary, count_org_owners, require_permission
from stoa_core.config import get_settings
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.security.permissions import SYSTEM_ROLE_OWNER, SYSTEM_ROLE_VIEWER

router = APIRouter(prefix="/v1/team", tags=["team"])


class ProfileHints(BaseModel):
    role_type: str | None = None
    job_title: str | None = None
    department: str | None = None
    notes: str | None = None


class InviteCreate(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    role_id: str | None = None
    role: str | None = Field(default=None, pattern="^(admin|analyst|viewer)$")
    profile_hints: ProfileHints | None = None


class InviteAccept(BaseModel):
    token: str = Field(min_length=16)


class MemberRoleUpdate(BaseModel):
    role_id: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _send_supabase_invite(email: str, invite_url: str) -> None:
    sb = get_supabase_admin()
    try:
        sb.auth.admin.invite_user_by_email(email, {"redirect_to": invite_url})
    except Exception:
        return


def _resolve_role_id(sb: Any, org_id: str, role_id: str | None, role_text: str | None) -> tuple[str, str]:
    if role_id:
        res = sb.table("org_roles").select("id, role_key, permissions").eq("id", role_id).eq("org_id", org_id).limit(1).execute()
        row = (res.data or [None])[0]
        if not row:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Role not found")
        return row["id"], row.get("role_key") or "custom"
    key = role_text or "viewer"
    res = sb.table("org_roles").select("id, role_key").eq("org_id", org_id).eq("role_key", key).limit(1).execute()
    row = (res.data or [None])[0]
    if not row:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"System role {key} not found")
    return row["id"], row["role_key"]


@router.get("/members")
def list_members(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "team:read")
    sb = get_supabase_admin()
    members_res = (
        sb.table("memberships")
        .select("id, user_id, role, role_id, created_at, org_roles(id, name, role_key)")
        .eq("org_id", scope.org_id)
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
                "role_name": (m.get("org_roles") or {}).get("name"),
                "profile": profiles.get(m["user_id"], {}),
            }
            for m in members
        ]
    }


@router.patch("/members/{member_id}")
def update_member_role(member_id: str, body: MemberRoleUpdate, scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "team:assign_roles")
    sb = get_supabase_admin()
    target = (
        sb.table("memberships")
        .select("id, user_id, role_id, org_roles(role_key)")
        .eq("id", member_id)
        .eq("org_id", scope.org_id)
        .limit(1)
        .execute()
    )
    membership = (target.data or [None])[0]
    if not membership:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    if membership["user_id"] == scope.user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot change your own role")
    new_role = (
        sb.table("org_roles").select("id, role_key, permissions").eq("id", body.role_id).eq("org_id", scope.org_id).limit(1).execute()
    )
    role_row = (new_role.data or [None])[0]
    if not role_row:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Role not found")
    if role_row.get("role_key") == SYSTEM_ROLE_OWNER and not scope.is_owner:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only owners can assign the owner role")
    if (membership.get("org_roles") or {}).get("role_key") == SYSTEM_ROLE_OWNER:
        if not scope.is_owner:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Only owners can change an owner membership")
        if count_org_owners(scope.org_id) <= 1 and role_row.get("role_key") != SYSTEM_ROLE_OWNER:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Transfer ownership before demoting the last owner")
    if not scope.is_owner:
        assert_permission_boundary(scope, set(role_row.get("permissions") or []))
    sb.table("memberships").update({"role_id": body.role_id, "role": role_row.get("role_key") or "custom"}).eq("id", member_id).execute()
    write_audit(scope.org_id, scope.user_id, "member.role_changed", "membership", member_id, {"role_id": body.role_id})
    return {"updated": True}


@router.delete("/members/{member_id}")
def remove_member(member_id: str, scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "team:remove")
    sb = get_supabase_admin()
    target = (
        sb.table("memberships")
        .select("id, user_id, org_roles(role_key)")
        .eq("id", member_id)
        .eq("org_id", scope.org_id)
        .limit(1)
        .execute()
    )
    membership = (target.data or [None])[0]
    if not membership:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    if membership["user_id"] == scope.user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Use leave organization instead")
    target_is_owner = (membership.get("org_roles") or {}).get("role_key") == SYSTEM_ROLE_OWNER
    if target_is_owner and not scope.is_owner:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only owners can remove another owner")
    if target_is_owner and count_org_owners(scope.org_id) <= 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot remove the last owner")
    sb.table("memberships").delete().eq("id", member_id).execute()
    write_audit(scope.org_id, scope.user_id, "member.removed", "membership", member_id)
    return {"removed": True}


@router.get("/invites")
def list_invites(scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "team:read")
    sb = get_supabase_admin()
    res = (
        sb.table("org_invites")
        .select("id, email, role, role_id, profile_hints, expires_at, accepted_at, revoked_at, created_at, org_roles(name, role_key)")
        .eq("org_id", scope.org_id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"invites": res.data or []}


@router.post("/invites")
def create_invite(body: InviteCreate, scope: OrgScope = Depends(verified_org_scope_dep)) -> dict[str, Any]:
    require_permission(scope, "team:invite")
    sb = get_supabase_admin()
    email = body.email.lower()
    role_id, role_key = _resolve_role_id(sb, scope.org_id, body.role_id, body.role)
    if not scope.is_owner:
        role_res = sb.table("org_roles").select("permissions").eq("id", role_id).limit(1).execute()
        role_perms = set((role_res.data or [{}])[0].get("permissions") or [])
        assert_permission_boundary(scope, role_perms)
    token = new_invite_token()
    token_hash = hash_invite_token(token)
    res = (
        sb.table("org_invites")
        .insert(
            {
                "org_id": scope.org_id,
                "email": email,
                "role": role_key if role_key in {SYSTEM_ROLE_OWNER, "admin", "analyst", "viewer"} else "viewer",
                "role_id": role_id,
                "token_hash": token_hash,
                "invited_by": scope.user_id,
                "expires_at": invite_expires_at(),
                "profile_hints": (body.profile_hints.model_dump(exclude_none=True) if body.profile_hints else {}),
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
    write_audit(scope.org_id, scope.user_id, "member.invited", "org_invite", invite["id"], {"email": email, "role_id": role_id})
    response: dict[str, Any] = {"invite": {k: v for k, v in invite.items() if k != "token_hash"}}
    if not settings.is_production:
        response["invite_url"] = invite_url
    return response


@router.post("/invites/{invite_id}/revoke")
def revoke_invite(invite_id: str, scope: OrgScope = Depends(require_onboarded_scope)) -> dict[str, Any]:
    require_permission(scope, "team:invite")
    sb = get_supabase_admin()
    res = (
        sb.table("org_invites")
        .update({"revoked_at": _now().isoformat()})
        .eq("id", invite_id)
        .eq("org_id", scope.org_id)
        .execute()
    )
    invite = (res.data or [None])[0]
    if not invite:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite not found")
    write_audit(scope.org_id, scope.user_id, "member.invite_revoked", "org_invite", invite_id)
    return {"invite": {k: v for k, v in invite.items() if k != "token_hash"}}


@router.post("/invites/accept")
def accept_invite(body: InviteAccept, claims: dict[str, Any] = Depends(verify_supabase_jwt_payload_verified)) -> dict[str, Any]:
    user_id = str(claims["sub"])
    get_or_create_user_profile(user_id, claims)
    email = email_from_claims(claims)
    token_hash = hash_invite_token(body.token)
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

    org_id = invite["org_id"]
    role_id = invite.get("role_id")
    role_key = invite.get("role") or SYSTEM_ROLE_VIEWER
    role_degraded = False
    if role_id:
        role_check = sb.table("org_roles").select("id, role_key").eq("id", role_id).eq("org_id", org_id).limit(1).execute()
        if not role_check.data:
            viewer = sb.table("org_roles").select("id, role_key").eq("org_id", org_id).eq("role_key", SYSTEM_ROLE_VIEWER).limit(1).execute()
            viewer_row = (viewer.data or [None])[0]
            role_id = viewer_row["id"] if viewer_row else None
            role_key = SYSTEM_ROLE_VIEWER
            role_degraded = True

    existing = (
        sb.table("memberships")
        .select("id")
        .eq("user_id", user_id)
        .eq("org_id", org_id)
        .limit(1)
        .execute()
    )
    if existing.data:
        sb.table("memberships").update({"role_id": role_id, "role": role_key}).eq("id", existing.data[0]["id"]).execute()
    else:
        sb.table("memberships").insert(
            {"org_id": org_id, "user_id": user_id, "role": role_key, "role_id": role_id}
        ).execute()

    hints = invite.get("profile_hints") or {}
    if hints:
        profile = sb.table("user_profiles").select("metadata").eq("user_id", user_id).limit(1).execute()
        meta = (profile.data or [{}])[0].get("metadata") or {}
        meta["invite_profile_hints"] = hints
        if hints.get("job_title") and not meta.get("job_title"):
            sb.table("user_profiles").update(
                {
                    "metadata": meta,
                    "job_title": hints.get("job_title"),
                    "role_type": hints.get("role_type") or None,
                }
            ).eq("user_id", user_id).execute()
        else:
            sb.table("user_profiles").update({"metadata": meta}).eq("user_id", user_id).execute()

    sb.table("user_profiles").update({"last_active_org_id": org_id}).eq("user_id", user_id).execute()
    accepted_at = _now().isoformat()
    sb.table("org_invites").update({"accepted_by": user_id, "accepted_at": accepted_at}).eq("id", invite["id"]).execute()
    write_audit(org_id, user_id, "member.joined", "org_invite", invite["id"], {"email": email, "role_id": role_id})
    return {
        "accepted": True,
        "org_id": org_id,
        "role": role_key,
        "role_id": role_id,
        "role_degraded": role_degraded,
    }
