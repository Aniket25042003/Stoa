"""
File: services/api/app/deps/org_scope.py
Layer: FastAPI Dependencies
Purpose: Implements org scope behavior for the fastapi dependencies.
Dependencies: FastAPI, Supabase
"""


from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, Request, status

from app.deps.auth import verify_supabase_jwt, verify_supabase_jwt_payload_verified
from app.services.auth_state import onboarding_needed_for_user
from app.services.org_context import OrgScope, get_org_scope


def org_scope_dep(
    request: Request,
    user_id: str = Depends(verify_supabase_jwt),
) -> OrgScope:
    """Handles org scope dep logic for the surrounding Stoa workflow.

    Args:
        request (Request): Input value used by this workflow step.
        user_id (str): Input value used by this workflow step.

    Returns:
        OrgScope: Result produced for the caller.
    """
    return get_org_scope(request, user_id)


def verified_org_scope_dep(
    request: Request,
    claims: dict[str, Any] = Depends(verify_supabase_jwt_payload_verified),
) -> OrgScope:
    """Handles verified org scope dep logic for the surrounding Stoa workflow.

    Args:
        request (Request): Input value used by this workflow step.
        claims (dict[str, Any]): Input value used by this workflow step.

    Returns:
        OrgScope: Result produced for the caller.
    """
    return get_org_scope(request, str(claims["sub"]))


def require_onboarded_scope(
    request: Request,
    claims: dict[str, Any] = Depends(verify_supabase_jwt_payload_verified),
) -> OrgScope:
    """Handles require onboarded scope logic for the surrounding Stoa workflow.

    Args:
        request (Request): Input value used by this workflow step.
        claims (dict[str, Any]): Input value used by this workflow step.

    Returns:
        OrgScope: Result produced for the caller.
    """
    user_id = str(claims["sub"])
    if onboarding_needed_for_user(user_id, claims):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail={"code": "onboarding_required", "message": "Complete onboarding to access this resource."},
        )
    return get_org_scope(request, user_id)
