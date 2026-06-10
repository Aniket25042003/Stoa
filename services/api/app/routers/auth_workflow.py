from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from app.config import get_settings
from app.deps.auth import verify_supabase_jwt_payload
from app.deps.client_ip import trusted_client_ip
from app.deps.rate_limit import check_public_rate_limit
from app.services.auth_email import send_signup_confirmation_email
from app.services.auth_state import (
    get_membership_optional,
    get_or_create_user_profile,
    onboarding_needed,
    user_is_email_verified,
)
from stoa_core.db.supabase import get_supabase_admin

router = APIRouter(prefix="/v1/auth", tags=["auth-workflow"])


class SignupBody(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)
    next: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not re.fullmatch(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
            raise ValueError("Enter a valid email address.")
        return email


def _safe_next_path(raw: str | None) -> str:
    if not raw:
        return "/dashboard"
    if not raw.startswith("/") or raw.startswith("//") or "://" in raw or "\\" in raw:
        return "/dashboard"
    if not re.fullmatch(r"/[A-Za-z0-9/_-]*", raw):
        return "/dashboard"
    return raw


def _signup_error_message(message: str) -> str:
    lower = message.lower()
    if "password" in lower:
        return message
    if "email" in lower and "invalid" in lower:
        return "Enter a valid email address."
    return "Could not create account. Check your details or sign in."


@router.post("/signup")
def email_signup(body: SignupBody, request: Request) -> dict[str, str]:
    """Create an email/password user and send verification in a separate step."""
    check_public_rate_limit(
        trusted_client_ip(request),
        email=str(body.email),
        scope="auth_signup",
    )

    email = str(body.email).strip().lower()
    full_name = body.full_name.strip()
    sb = get_supabase_admin()

    try:
        sb.auth.admin.create_user(
            {
                "email": email,
                "password": body.password,
                "email_confirm": False,
                "user_metadata": {"full_name": full_name, "name": full_name},
            }
        )
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, _signup_error_message(str(exc))) from exc

    settings = get_settings()
    origin = (request.headers.get("origin") or settings.app_base_url).rstrip("/")
    next_path = _safe_next_path(body.next)
    email_redirect_to = f"{origin}/auth/callback?next={quote(next_path, safe='')}"

    try:
        send_signup_confirmation_email(email=email, email_redirect_to=email_redirect_to)
    except HTTPException as exc:
        return {
            "status": "created_email_pending",
            "detail": str(exc.detail),
        }

    return {"status": "created"}


class ResendVerificationBody(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    next: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not re.fullmatch(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
            raise ValueError("Enter a valid email address.")
        return email


@router.post("/resend-verification")
def resend_verification(body: ResendVerificationBody, request: Request) -> dict[str, str]:
    check_public_rate_limit(
        trusted_client_ip(request),
        email=body.email,
        scope="auth_resend",
    )

    settings = get_settings()
    origin = (request.headers.get("origin") or settings.app_base_url).rstrip("/")
    next_path = _safe_next_path(body.next)
    email_redirect_to = f"{origin}/auth/callback?next={quote(next_path, safe='')}"
    send_signup_confirmation_email(email=body.email, email_redirect_to=email_redirect_to)
    return {"status": "sent"}


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
