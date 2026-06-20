"""
File: services/api/app/services/auth_email.py
Layer: FastAPI Service Layer
Purpose: Contains reusable backend business logic shared by routes and workers.
Dependencies: FastAPI, Supabase, stoa_core
"""

from __future__ import annotations

import logging

from fastapi import HTTPException, status
from supabase_auth.errors import AuthApiError

from stoa_core.db.supabase import get_supabase_admin, get_supabase_anon

logger = logging.getLogger(__name__)


def _user_friendly_resend_error(message: str) -> str:
    """Handles  user friendly resend error logic for the surrounding Stoa workflow.

    Args:
        message (str): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    lower = message.lower()
    if "rate" in lower and "limit" in lower:
        return "Too many verification emails requested. Wait a few minutes and try again."
    if "smtp" in lower or "mail" in lower:
        return "Email could not be delivered. Check Supabase SMTP settings and Brevo sender verification."
    if "redirect" in lower:
        return "Email redirect URL is not allowed. Add your app callback URL in Supabase Auth URL settings."
    if "not found" in lower or "no user" in lower:
        return "No pending signup found for this email. Sign up again or use a different address."
    return message or "Could not send verification email."


def send_signup_confirmation_email(*, email: str, email_redirect_to: str) -> None:
    """Queue a signup confirmation email through Supabase Auth (anon API + custom SMTP)."""
    try:
        anon = get_supabase_anon()
    except RuntimeError as exc:
        raise HTTPException(
            status.HTTP_503_INTERNAL_SERVER_ERROR,
            "SUPABASE_ANON_KEY is not configured on the API. Copy NEXT_PUBLIC_SUPABASE_ANON_KEY from apps/web/.env.local into services/api/.env.",
        ) from exc
    try:
        anon.auth.resend(
            {
                "type": "signup",
                "email": email,
                "options": {"email_redirect_to": email_redirect_to},
            }
        )
        logger.info("Signup confirmation email requested for %s", email)
        return
    except AuthApiError as exc:
        logger.warning("Anon resend failed for %s: %s", email, exc)
        detail = _user_friendly_resend_error(str(exc))
    except Exception as exc:
        logger.exception("Unexpected resend failure for %s", email)
        raise HTTPException(
            status.HTTP_503_INTERNAL_SERVER_ERROR,
            "Could not send verification email.",
        ) from exc

    # Fallback for admin-created users when public resend rejects the request.
    admin = get_supabase_admin()
    try:
        admin.auth.admin.invite_user_by_email(email, {"redirect_to": email_redirect_to})
        logger.info("Invite confirmation email requested for %s", email)
        return
    except AuthApiError as exc:
        logger.warning("Invite fallback failed for %s: %s", email, exc)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail) from exc
    except Exception as exc:
        logger.exception("Invite fallback unexpected failure for %s", email)
        raise HTTPException(
            status.HTTP_503_INTERNAL_SERVER_ERROR,
            "Could not send verification email.",
        ) from exc
