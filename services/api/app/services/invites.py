"""
File: services/api/app/services/invites.py
Layer: FastAPI Service Layer
Purpose: Contains reusable backend business logic shared by routes and workers.
Dependencies: FastAPI
"""


from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.config import get_settings


def invite_pepper() -> str:
    """Handles invite pepper logic for the surrounding Stoa workflow.

    Returns:
        str: Result produced for the caller.
    """
    settings = get_settings()
    pepper = settings.invite_token_pepper.strip()
    if pepper:
        return pepper
    if settings.is_production:
        raise HTTPException(500, "Invite configuration error")
    return "dev-only-insecure-pepper"


def hash_invite_token(token: str) -> str:
    """Handles hash invite token logic for the surrounding Stoa workflow.

    Args:
        token (str): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    return hashlib.sha256(f"{token}.{invite_pepper()}".encode("utf-8")).hexdigest()


def new_invite_token() -> str:
    """Handles new invite token logic for the surrounding Stoa workflow.

    Returns:
        str: Result produced for the caller.
    """
    return secrets.token_urlsafe(32)


def invite_expires_at(days: int = 7) -> str:
    """Handles invite expires at logic for the surrounding Stoa workflow.

    Args:
        days (int): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
