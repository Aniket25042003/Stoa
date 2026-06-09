"""Organization membership resolution."""

from __future__ import annotations

from fastapi import HTTPException, status

from stoa_core.db.supabase import get_supabase_admin

ROLE_HIERARCHY = {"owner": 4, "admin": 3, "analyst": 2, "viewer": 1}


def get_user_membership(user_id: str) -> dict:
    sb = get_supabase_admin()
    res = (
        sb.table("memberships")
        .select(
            "id, org_id, role, created_at, "
            "organizations(id, name, slug, website_url, industry, profile, onboarding_completed_at)"
        )
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No organization found for user")
    return rows[0]


def require_role(membership: dict, min_role: str) -> None:
    role = membership.get("role", "viewer")
    if ROLE_HIERARCHY.get(role, 0) < ROLE_HIERARCHY.get(min_role, 0):
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Requires {min_role} role")


def ensure_org_access(user_id: str, org_id: str, *, min_role: str | None = None) -> dict:
    membership = get_user_membership(user_id)
    if membership.get("org_id") != org_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Organization access denied")
    if min_role:
        require_role(membership, min_role)
    return membership
