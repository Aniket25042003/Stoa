"""Organization role seeding and resolution helpers."""

from __future__ import annotations

from typing import Any

from stoa_core.security.permissions import (
    SYSTEM_ROLE_ADMIN,
    SYSTEM_ROLE_ANALYST,
    SYSTEM_ROLE_OWNER,
    SYSTEM_ROLE_VIEWER,
    SYSTEM_ROLES,
    builtin_role_permissions,
    is_owner_role,
)


def system_role_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "Owner",
            "role_key": SYSTEM_ROLE_OWNER,
            "description": "Full organization access including deletion and ownership transfer.",
            "permissions": builtin_role_permissions(SYSTEM_ROLE_OWNER),
            "is_system": True,
        },
        {
            "name": "Admin",
            "role_key": SYSTEM_ROLE_ADMIN,
            "description": "Manage team, data, and intelligence; cannot manage custom roles.",
            "permissions": builtin_role_permissions(SYSTEM_ROLE_ADMIN),
            "is_system": True,
        },
        {
            "name": "Analyst",
            "role_key": SYSTEM_ROLE_ANALYST,
            "description": "Create and edit content, run scans, and ask questions.",
            "permissions": builtin_role_permissions(SYSTEM_ROLE_ANALYST),
            "is_system": True,
        },
        {
            "name": "Viewer",
            "role_key": SYSTEM_ROLE_VIEWER,
            "description": "Read-only access to organization data.",
            "permissions": builtin_role_permissions(SYSTEM_ROLE_VIEWER),
            "is_system": True,
        },
    ]


def seed_system_roles_for_org(
    sb: Any, org_id: str, *, created_by: str | None = None
) -> dict[str, str]:
    """Insert system roles for an org. Returns role_key -> role_id map."""
    role_map: dict[str, str] = {}
    for definition in system_role_definitions():
        res = (
            sb.table("org_roles")
            .insert(
                {
                    "org_id": org_id,
                    "name": definition["name"],
                    "role_key": definition["role_key"],
                    "description": definition["description"],
                    "permissions": definition["permissions"],
                    "is_system": True,
                    "created_by": created_by,
                }
            )
            .execute()
        )
        row = (res.data or [None])[0]
        if row:
            role_map[definition["role_key"]] = row["id"]
    return role_map


def resolve_permissions(role_row: dict[str, Any] | None) -> set[str]:
    if not role_row:
        return set()
    role_key = role_row.get("role_key")
    if is_owner_role(role_key):
        return set(builtin_role_permissions(SYSTEM_ROLE_OWNER))
    perms = role_row.get("permissions") or []
    return set(perms)


def role_key_from_membership(membership: dict[str, Any]) -> str:
    org_roles = membership.get("org_roles") or {}
    if isinstance(org_roles, dict) and org_roles.get("role_key"):
        return str(org_roles["role_key"])
    role = membership.get("role")
    if role in SYSTEM_ROLES:
        return str(role)
    return "custom"
