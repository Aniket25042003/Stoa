"""Custom organization roles (IAM-style)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.deps.org_scope import org_scope_dep, verified_org_scope_dep
from app.services.audit import write_audit
from app.services.org_context import OrgScope, assert_permission_boundary, require_permission
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.security.permissions import OWNER_RESERVED, catalog_for_ui, grantable_permissions

router = APIRouter(prefix="/v1/roles", tags=["roles"])


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    permissions: list[str] = Field(min_length=1)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    permissions: list[str] | None = None


class RoleDelete(BaseModel):
    reassign_to_role_id: str | None = None


def _validate_permissions(perms: list[str]) -> list[str]:
    allowed = set(grantable_permissions())
    invalid = [p for p in perms if p not in allowed]
    if invalid:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid permissions: {', '.join(invalid)}")
    reserved = [p for p in perms if p in OWNER_RESERVED]
    if reserved:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Owner-reserved permissions cannot be granted")
    return sorted(set(perms))


@router.get("/catalog")
def get_permission_catalog() -> dict[str, Any]:
    return {"groups": catalog_for_ui(), "grantable": grantable_permissions()}


@router.get("")
def list_roles(scope: OrgScope = Depends(org_scope_dep)) -> dict[str, Any]:
    require_permission(scope, "team:read")
    sb = get_supabase_admin()
    res = (
        sb.table("org_roles")
        .select("id, org_id, name, role_key, description, permissions, is_system, created_at, updated_at")
        .eq("org_id", scope.org_id)
        .order("is_system", desc=True)
        .order("name", desc=False)
        .execute()
    )
    return {"roles": res.data or []}


@router.post("")
def create_role(body: RoleCreate, scope: OrgScope = Depends(verified_org_scope_dep)) -> dict[str, Any]:
    require_permission(scope, "roles:manage")
    perms = _validate_permissions(body.permissions)
    assert_permission_boundary(scope, set(perms))
    sb = get_supabase_admin()
    res = (
        sb.table("org_roles")
        .insert(
            {
                "org_id": scope.org_id,
                "name": body.name.strip(),
                "role_key": "custom",
                "description": body.description,
                "permissions": perms,
                "is_system": False,
                "created_by": scope.user_id,
            }
        )
        .execute()
    )
    role = (res.data or [None])[0]
    if not role:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to create role")
    write_audit(scope.org_id, scope.user_id, "role.created", "org_role", role["id"], {"name": body.name})
    return {"role": role}


@router.patch("/{role_id}")
def update_role(role_id: str, body: RoleUpdate, scope: OrgScope = Depends(verified_org_scope_dep)) -> dict[str, Any]:
    require_permission(scope, "roles:manage")
    sb = get_supabase_admin()
    existing = (
        sb.table("org_roles").select("*").eq("id", role_id).eq("org_id", scope.org_id).limit(1).execute()
    )
    role = (existing.data or [None])[0]
    if not role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    if role.get("is_system"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "System roles cannot be modified")
    if not scope.is_owner:
        existing_perms = set(role.get("permissions") or [])
        if not existing_perms.issubset(scope.permissions):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot edit roles with permissions beyond your own")

    updates: dict[str, Any] = {}
    if body.name is not None:
        updates["name"] = body.name.strip()
    if body.description is not None:
        updates["description"] = body.description
    if body.permissions is not None:
        perms = _validate_permissions(body.permissions)
        assert_permission_boundary(scope, set(perms))
        updates["permissions"] = perms
    if not updates:
        return {"role": role}
    res = sb.table("org_roles").update(updates).eq("id", role_id).execute()
    updated = (res.data or [role])[0]
    write_audit(scope.org_id, scope.user_id, "role.updated", "org_role", role_id, updates)
    return {"role": updated}


@router.delete("/{role_id}")
def delete_role(
    role_id: str,
    body: RoleDelete | None = None,
    scope: OrgScope = Depends(verified_org_scope_dep),
) -> dict[str, Any]:
    body = body or RoleDelete()
    require_permission(scope, "roles:manage")
    sb = get_supabase_admin()
    existing = (
        sb.table("org_roles").select("*").eq("id", role_id).eq("org_id", scope.org_id).limit(1).execute()
    )
    role = (existing.data or [None])[0]
    if not role:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    if role.get("is_system"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "System roles cannot be deleted")

    members = sb.table("memberships").select("id", count="exact").eq("org_id", scope.org_id).eq("role_id", role_id).execute()
    invites = sb.table("org_invites").select("id", count="exact").eq("org_id", scope.org_id).eq("role_id", role_id).is_("accepted_at", "null").is_("revoked_at", "null").execute()
    in_use = (members.count or 0) + (invites.count or 0)
    if in_use and not body.reassign_to_role_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Role in use; provide reassign_to_role_id")

    if body.reassign_to_role_id:
        target = (
            sb.table("org_roles").select("id").eq("id", body.reassign_to_role_id).eq("org_id", scope.org_id).limit(1).execute()
        )
        if not target.data:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Reassignment role not found")
        sb.table("memberships").update({"role_id": body.reassign_to_role_id}).eq("org_id", scope.org_id).eq("role_id", role_id).execute()
        sb.table("org_invites").update({"role_id": body.reassign_to_role_id}).eq("org_id", scope.org_id).eq("role_id", role_id).execute()

    sb.table("org_roles").delete().eq("id", role_id).execute()
    write_audit(scope.org_id, scope.user_id, "role.deleted", "org_role", role_id)
    return {"deleted": True}
