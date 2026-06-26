"""
File: services/core/src/stoa_core/integrations/google_oauth.py
Layer: Core Integration Connectors
Purpose: Shared Google OAuth authorize, token exchange, and refresh for GA4 and Drive.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import httpx

from stoa_core.config import get_settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

GA4_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.readonly"


def _settings():
    return get_settings()


def google_oauth_configured() -> bool:
    s = _settings()
    return bool(s.google_client_id.strip() and s.google_client_secret.strip())


def google_authorize_url(state: str, redirect_uri: str, scopes: list[str]) -> str | None:
    s = _settings()
    if not google_oauth_configured():
        return None
    params = {
        "client_id": s.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_google_code(code: str, redirect_uri: str) -> dict[str, Any]:
    s = _settings()
    with httpx.Client(timeout=30) as client:
        res = client.post(
            GOOGLE_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": s.google_client_id,
                "client_secret": s.google_client_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )
        res.raise_for_status()
        data = res.json()
    return {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token"),
        "expires_in": data.get("expires_in"),
    }


def refresh_google_token(credentials: dict[str, Any]) -> dict[str, Any]:
    refresh = credentials.get("refresh_token")
    if not refresh:
        return credentials
    s = _settings()
    with httpx.Client(timeout=30) as client:
        res = client.post(
            GOOGLE_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": s.google_client_id,
                "client_secret": s.google_client_secret,
                "refresh_token": refresh,
            },
        )
        if res.status_code >= 400:
            return credentials
        data = res.json()
    credentials = dict(credentials)
    credentials["access_token"] = data["access_token"]
    if data.get("refresh_token"):
        credentials["refresh_token"] = data["refresh_token"]
    if data.get("expires_in"):
        credentials["expires_in"] = data["expires_in"]
    return credentials
