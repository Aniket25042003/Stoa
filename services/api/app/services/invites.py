"""Organization invite token helpers."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.config import get_settings


def invite_pepper() -> str:
    settings = get_settings()
    pepper = settings.invite_token_pepper.strip()
    if pepper:
        return pepper
    if settings.is_production:
        raise HTTPException(500, "Invite configuration error")
    return "dev-only-insecure-pepper"


def hash_invite_token(token: str) -> str:
    return hashlib.sha256(f"{token}.{invite_pepper()}".encode("utf-8")).hexdigest()


def new_invite_token() -> str:
    return secrets.token_urlsafe(32)


def invite_expires_at(days: int = 7) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
