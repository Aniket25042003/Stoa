"""
File: services/api/app/services/org_context.py
Layer: FastAPI Service Layer
Purpose: Contains reusable backend business logic shared by routes and workers.
Dependencies: FastAPI, Supabase, stoa_core
"""


from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, Request, status

from stoa_core.db.supabase import get_supabase_admin
from stoa_core.org.roles import resolve_permissions, role_key_from_membership
from stoa_core.security.permissions import (
    SYSTEM_ROLE_OWNER,
    is_owner_role,
    permission_set_satisfies,
)

ROLE_HIERARCHY = {"owner": 4, "admin": 3, "analyst": 2, "viewer": 1}

_MEMBERSHIP_SELECT = (
    "id, org_id, user_id, role, role_id, created_at, "
    "org_roles(id, name, role_key, permissions, is_system), "
    "organizations(id, name, slug, website_url, industry, profile, onboarding_completed_at)"
)


@dataclass(frozen=True)
class OrgScope:
    """Manage OrgScope behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    user_id: str
    org_id: str
    membership: dict[str, Any]
    role_key: str
    role_name: str
    permissions: frozenset[str]
    is_owner: bool

    @property
    def org(self) -> dict[str, Any]:
        """Handles org logic for the surrounding Stoa workflow.

        Returns:
            dict[str, Any]: Result produced for the caller.
        """
        return self.membership.get("organizations") or {}


def _resolve_org_id(request: Request, user_id: str) -> str | None:
    """Handles  resolve org id logic for the surrounding Stoa workflow.

    Args:
        request (Request): Input value used by this workflow step.
        user_id (str): Input value used by this workflow step.

    Returns:
        str | None: Result produced for the caller.
    """
    header = (request.headers.get("x-org-id") or "").strip()
    if header:
        try:
            return str(uuid.UUID(header))
        except ValueError as exc:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Invalid X-Org-Id header"
            ) from exc
    sb = get_supabase_admin()
    profile = sb.table("user_profiles").select("last_active_org_id").eq("user_id", user_id).limit(1).execute()
    row = (profile.data or [None])[0]
    if row and row.get("last_active_org_id"):
        return str(row["last_active_org_id"])
    memberships = sb.table("memberships").select("org_id").eq("user_id", user_id).execute()
    rows = memberships.data or []
    if len(rows) == 1:
        return str(rows[0]["org_id"])
    return None


def _load_membership(user_id: str, org_id: str) -> dict[str, Any] | None:
    """Handles  load membership logic for the surrounding Stoa workflow.

    Args:
        user_id (str): Input value used by this workflow step.
        org_id (str): Input value used by this workflow step.

    Returns:
        dict[str, Any] | None: Result produced for the caller.
    """
    sb = get_supabase_admin()
    res = (
        sb.table("memberships")
        .select(_MEMBERSHIP_SELECT)
        .eq("user_id", user_id)
        .eq("org_id", org_id)
        .limit(1)
        .execute()
    )
    return (res.data or [None])[0]


def list_user_memberships(user_id: str) -> list[dict[str, Any]]:
    """Handles list user memberships logic for the surrounding Stoa workflow.

    Args:
        user_id (str): Input value used by this workflow step.

    Returns:
        list[dict[str, Any]]: Result produced for the caller.
    """
    sb = get_supabase_admin()
    res = (
        sb.table("memberships")
        .select(_MEMBERSHIP_SELECT)
        .eq("user_id", user_id)
        .order("created_at", desc=False)
        .execute()
    )
    return res.data or []


def build_org_scope(request: Request, user_id: str, *, org_id: str | None = None) -> OrgScope:
    """Handles build org scope logic for the surrounding Stoa workflow.

    Args:
        request (Request): Input value used by this workflow step.
        user_id (str): Input value used by this workflow step.
        org_id (str | None): Input value used by this workflow step.

    Returns:
        OrgScope: Result produced for the caller.
    """
    resolved_org_id = org_id or _resolve_org_id(request, user_id)
    if not resolved_org_id:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={"code": "org_selection_required", "message": "Select an organization to continue."},
        )
    membership = _load_membership(user_id, resolved_org_id)
    if not membership:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Organization access denied")
    role_row = membership.get("org_roles") or {}
    role_key = role_key_from_membership(membership)
    perms = resolve_permissions(role_row if isinstance(role_row, dict) else None)
    return OrgScope(
        user_id=user_id,
        org_id=resolved_org_id,
        membership=membership,
        role_key=role_key,
        role_name=str(role_row.get("name") or membership.get("role") or "Member"),
        permissions=frozenset(perms),
        is_owner=is_owner_role(role_key),
    )


def get_org_scope(request: Request, user_id: str) -> OrgScope:
    """Handles get org scope logic for the surrounding Stoa workflow.

    Args:
        request (Request): Input value used by this workflow step.
        user_id (str): Input value used by this workflow step.

    Returns:
        OrgScope: Result produced for the caller.
    """
    return build_org_scope(request, user_id)


def get_user_membership(user_id: str, org_id: str | None = None) -> dict[str, Any]:
    """Backward-compatible helper; prefer get_org_scope in routers."""
    sb = get_supabase_admin()
    if org_id:
        membership = _load_membership(user_id, org_id)
        if not membership:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No organization found for user")
        return membership
    res = (
        sb.table("memberships")
        .select(_MEMBERSHIP_SELECT)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No organization found for user")
    return rows[0]


def require_permission(scope: OrgScope, perm: str) -> None:
    """Handles require permission logic for the surrounding Stoa workflow.

    Args:
        scope (OrgScope): Input value used by this workflow step.
        perm (str): Input value used by this workflow step.
    """
    if scope.is_owner or perm in scope.permissions:
        return
    raise HTTPException(status.HTTP_403_FORBIDDEN, f"Requires permission: {perm}")


def require_any_permission(scope: OrgScope, *perms: str) -> None:
    """Handles require any permission logic for the surrounding Stoa workflow.

    Args:
        scope (OrgScope): Input value used by this workflow step.
    """
    if scope.is_owner:
        return
    if any(p in scope.permissions for p in perms):
        return
    raise HTTPException(status.HTTP_403_FORBIDDEN, f"Requires one of: {', '.join(perms)}")


def require_role(membership: dict[str, Any], min_role: str) -> None:
    """Handles require role logic for the surrounding Stoa workflow.

    Args:
        membership (dict[str, Any]): Input value used by this workflow step.
        min_role (str): Input value used by this workflow step.
    """
    role_key = role_key_from_membership(membership)
    if ROLE_HIERARCHY.get(role_key, 0) < ROLE_HIERARCHY.get(min_role, 0):
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Requires {min_role} role")


def require_owner(scope: OrgScope) -> None:
    """Handles require owner logic for the surrounding Stoa workflow.

    Args:
        scope (OrgScope): Input value used by this workflow step.
    """
    if not scope.is_owner:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Owner access required")


def ensure_org_access(user_id: str, org_id: str, *, min_role: str | None = None) -> dict[str, Any]:
    """Handles ensure org access logic for the surrounding Stoa workflow.

    Args:
        user_id (str): Input value used by this workflow step.
        org_id (str): Input value used by this workflow step.
        min_role (str | None): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    membership = _load_membership(user_id, org_id)
    if not membership:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Organization access denied")
    if min_role:
        require_role(membership, min_role)
    return membership


def assert_permission_boundary(actor: OrgScope, requested_permissions: set[str]) -> None:
    """Handles assert permission boundary logic for the surrounding Stoa workflow.

    Args:
        actor (OrgScope): Input value used by this workflow step.
        requested_permissions (set[str]): Input value used by this workflow step.
    """
    if actor.is_owner:
        return
    if not permission_set_satisfies(set(actor.permissions), requested_permissions):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot grant permissions beyond your own role")


def set_last_active_org(user_id: str, org_id: str) -> None:
    """Handles set last active org logic for the surrounding Stoa workflow.

    Args:
        user_id (str): Input value used by this workflow step.
        org_id (str): Input value used by this workflow step.
    """
    sb = get_supabase_admin()
    sb.table("user_profiles").update({"last_active_org_id": org_id}).eq("user_id", user_id).execute()


def count_org_owners(org_id: str) -> int:
    """Handles count org owners logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.

    Returns:
        int: Result produced for the caller.
    """
    sb = get_supabase_admin()
    res = (
        sb.table("memberships")
        .select("id, org_roles!inner(role_key)", count="exact")
        .eq("org_id", org_id)
        .eq("org_roles.role_key", SYSTEM_ROLE_OWNER)
        .execute()
    )
    return res.count or 0
