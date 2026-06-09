from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.deps.auth import verify_supabase_jwt_payload
from app.services.auth_state import (
    get_membership_optional,
    get_or_create_user_profile,
    onboarding_needed,
    user_is_email_verified,
)

router = APIRouter(prefix="/v1/auth", tags=["auth-workflow"])


@router.get("/session-state")
def get_session_state(claims: dict[str, Any] = Depends(verify_supabase_jwt_payload)) -> dict[str, Any]:
    user_id = str(claims["sub"])
    profile = get_or_create_user_profile(user_id, claims)
    membership = get_membership_optional(user_id)
    org = (membership or {}).get("organizations")
    email_verified = user_is_email_verified(user_id, claims)

    return {
        "user": {
            "id": user_id,
            "email": profile.get("email"),
            "auth_provider": profile.get("auth_provider"),
            "email_verified": email_verified,
        },
        "user_profile": profile,
        "membership": (
            {
                "id": membership["id"],
                "org_id": membership["org_id"],
                "role": membership["role"],
            }
            if membership
            else None
        ),
        "org": org,
        "needs_email_verification": not email_verified,
        "needs_onboarding": onboarding_needed(profile, membership),
    }
