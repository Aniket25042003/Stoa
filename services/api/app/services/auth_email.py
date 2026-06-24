"""
File: services/api/app/services/auth_email.py
Layer: FastAPI Service Layer
Purpose: Contains reusable backend business logic shared by routes and workers.
Dependencies: FastAPI, Supabase, stoa_core
"""

from __future__ import annotations

import logging

from supabase_auth.errors import AuthApiError

from stoa_core.db.supabase import get_supabase_admin, get_supabase_anon

logger = logging.getLogger(__name__)


def send_signup_confirmation_email(*, email: str, email_redirect_to: str) -> None:
    """Queue a signup confirmation email through Supabase Auth (anon API + custom SMTP).

    Always completes without raising user-facing errors so callers can return a
    generic response (prevents email enumeration).
    """
    try:
        anon = get_supabase_anon()
    except RuntimeError as exc:
        logger.error("SUPABASE_ANON_KEY is not configured: %s", exc)
        return
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
    except Exception:
        logger.exception("Unexpected resend failure for %s", email)
        return

    # Fallback for admin-created users when public resend rejects the request.
    admin = get_supabase_admin()
    try:
        admin.auth.admin.invite_user_by_email(email, {"redirect_to": email_redirect_to})
        logger.info("Invite confirmation email requested for %s", email)
    except AuthApiError as exc:
        logger.warning("Invite fallback failed for %s: %s", email, exc)
    except Exception:
        logger.exception("Invite fallback unexpected failure for %s", email)
