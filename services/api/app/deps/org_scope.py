"""FastAPI dependencies for org scope and onboarding gates."""

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
    return get_org_scope(request, user_id)


def verified_org_scope_dep(
    request: Request,
    claims: dict[str, Any] = Depends(verify_supabase_jwt_payload_verified),
) -> OrgScope:
    return get_org_scope(request, str(claims["sub"]))


def require_onboarded_scope(
    request: Request,
    claims: dict[str, Any] = Depends(verify_supabase_jwt_payload_verified),
) -> OrgScope:
    user_id = str(claims["sub"])
    if onboarding_needed_for_user(user_id, claims):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail={"code": "onboarding_required", "message": "Complete onboarding to access this resource."},
        )
    return get_org_scope(request, user_id)
