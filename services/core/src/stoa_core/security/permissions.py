"""
File: services/core/src/stoa_core/security/permissions.py
Layer: Core Security Utilities
Purpose: Implements permissions behavior for the core security utilities.
Dependencies: standard library / local modules
"""


from __future__ import annotations

from typing import Any

# Owner-reserved: never grantable to custom roles
OWNER_RESERVED = frozenset({"org:delete", "org:transfer_ownership"})

# All grantable permissions (resource:action)
PERMISSION_CATALOG: dict[str, list[str]] = {
    "documents": ["read", "write", "delete"],
    "data_sources": ["read", "write"],
    "intelligence": ["read", "rebuild"],
    "insights": ["read", "refresh"],
    "conversations": ["read", "ask"],
    "competitive": ["read", "manage", "scan"],
    "campaigns": ["read", "create", "edit"],
    "campaign_analysis": ["read", "refresh"],
    "alignment": ["read", "refresh"],
    "content": ["read", "create", "write", "delete"],
    "team": ["read", "invite", "remove", "assign_roles"],
    "roles": ["manage"],
    "org": ["update", "leave"],
    "audit": ["read"],
}

SYSTEM_ROLE_OWNER = "owner"
SYSTEM_ROLE_ADMIN = "admin"
SYSTEM_ROLE_ANALYST = "analyst"
SYSTEM_ROLE_VIEWER = "viewer"

SYSTEM_ROLES = frozenset(
    {SYSTEM_ROLE_OWNER, SYSTEM_ROLE_ADMIN, SYSTEM_ROLE_ANALYST, SYSTEM_ROLE_VIEWER}
)


def all_permissions() -> list[str]:
    """Handles all permissions logic for the surrounding Stoa workflow.

    Returns:
        list[str]: Result produced for the caller.
    """
    perms: list[str] = []
    for resource, actions in PERMISSION_CATALOG.items():
        for action in actions:
            perms.append(f"{resource}:{action}")
    perms.extend(sorted(OWNER_RESERVED))
    return perms


def grantable_permissions() -> list[str]:
    """Handles grantable permissions logic for the surrounding Stoa workflow.

    Returns:
        list[str]: Result produced for the caller.
    """
    return [p for p in all_permissions() if p not in OWNER_RESERVED]


def _read_all() -> list[str]:
    """Handles  read all logic for the surrounding Stoa workflow.

    Returns:
        list[str]: Result produced for the caller.
    """
    return [p for p in all_permissions() if p.endswith(":read")]


def _analyst_write_perms() -> list[str]:
    """Handles  analyst write perms logic for the surrounding Stoa workflow.

    Returns:
        list[str]: Result produced for the caller.
    """
    return [
        "documents:read",
        "documents:write",
        "data_sources:read",
        "data_sources:write",
        "intelligence:read",
        "insights:read",
        "conversations:read",
        "conversations:ask",
        "competitive:read",
        "competitive:manage",
        "competitive:scan",
        "campaigns:read",
        "campaigns:create",
        "campaigns:edit",
        "campaign_analysis:read",
        "campaign_analysis:refresh",
        "alignment:read",
        "alignment:refresh",
        "content:read",
        "content:create",
        "content:write",
        "content:delete",
        "team:read",
        "org:leave",
    ]


def builtin_role_permissions(role_key: str) -> list[str]:
    """Handles builtin role permissions logic for the surrounding Stoa workflow.

    Args:
        role_key (str): Input value used by this workflow step.

    Returns:
        list[str]: Result produced for the caller.
    """
    if role_key == SYSTEM_ROLE_OWNER:
        return all_permissions()
    if role_key == SYSTEM_ROLE_ADMIN:
        return [p for p in grantable_permissions() if p != "roles:manage"]
    if role_key == SYSTEM_ROLE_ANALYST:
        return _analyst_write_perms()
    if role_key == SYSTEM_ROLE_VIEWER:
        return _read_all() + ["org:leave"]
    return []


def is_owner_role(role_key: str | None) -> bool:
    """Handles is owner role logic for the surrounding Stoa workflow.

    Args:
        role_key (str | None): Input value used by this workflow step.

    Returns:
        bool: Result produced for the caller.
    """
    return role_key == SYSTEM_ROLE_OWNER


def permissions_include(holder: set[str] | frozenset[str], required: str) -> bool:
    """Handles permissions include logic for the surrounding Stoa workflow.

    Args:
        holder (set[str] | frozenset[str]): Input value used by this workflow step.
        required (str): Input value used by this workflow step.

    Returns:
        bool: Result produced for the caller.
    """
    if required in holder:
        return True
    return False


def permission_set_satisfies(holder: set[str], required: set[str]) -> bool:
    """Handles permission set satisfies logic for the surrounding Stoa workflow.

    Args:
        holder (set[str]): Input value used by this workflow step.
        required (set[str]): Input value used by this workflow step.

    Returns:
        bool: Result produced for the caller.
    """
    return required.issubset(holder)


def catalog_for_ui() -> list[dict[str, Any]]:
    """Grouped permission catalog for the roles management UI."""
    groups: list[dict[str, Any]] = []
    labels = {
        "documents": "Documents",
        "data_sources": "Data sources",
        "intelligence": "Intelligence",
        "insights": "Insights",
        "conversations": "Conversations",
        "competitive": "Competitive",
        "campaigns": "Campaigns",
        "campaign_analysis": "Campaign Analysis",
        "alignment": "Sales–Marketing Alignment",
        "content": "Content Studio",
        "team": "Team",
        "roles": "Roles",
        "org": "Organization",
        "audit": "Audit",
    }
    for resource, actions in PERMISSION_CATALOG.items():
        perms = []
        for action in actions:
            key = f"{resource}:{action}"
            if key in OWNER_RESERVED:
                continue
            perms.append({"key": key, "action": action, "label": action.replace("_", " ").title()})
        if perms:
            groups.append(
                {
                    "resource": resource,
                    "label": labels.get(resource, resource.title()),
                    "permissions": perms,
                }
            )
    return groups
