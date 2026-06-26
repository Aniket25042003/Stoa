"""
File: services/core/src/stoa_core/integrations/oauth_refresh.py
Layer: Core Integration Connectors
Purpose: Shared OAuth token refresh before integration sync runs.
"""

from __future__ import annotations

from typing import Any

import httpx

from stoa_core.config import get_settings
from stoa_core.integrations.google_oauth import refresh_google_token


def _settings():
    return get_settings()


def refresh_hubspot_token(credentials: dict[str, Any]) -> dict[str, Any]:
    refresh = credentials.get("refresh_token")
    if not refresh:
        return credentials
    s = _settings()
    with httpx.Client(timeout=30) as client:
        res = client.post(
            "https://api.hubapi.com/oauth/v1/token",
            data={
                "grant_type": "refresh_token",
                "client_id": s.hubspot_client_id,
                "client_secret": s.hubspot_client_secret,
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
    return credentials


def refresh_salesforce_token(
    credentials: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    refresh = credentials.get("refresh_token")
    if not refresh:
        return credentials
    s = _settings()
    metadata = metadata or {}
    environment = metadata.get("environment", "production")
    login_host = "test.salesforce.com" if environment == "sandbox" else "login.salesforce.com"
    with httpx.Client(timeout=30) as client:
        res = client.post(
            f"https://{login_host}/services/oauth2/token",
            data={
                "grant_type": "refresh_token",
                "client_id": s.salesforce_client_id,
                "client_secret": s.salesforce_client_secret,
                "refresh_token": refresh,
            },
        )
        if res.status_code >= 400:
            return credentials
        data = res.json()
    credentials = dict(credentials)
    credentials["access_token"] = data["access_token"]
    if data.get("instance_url"):
        credentials["instance_url"] = data["instance_url"]
    return credentials


def refresh_zendesk_token(credentials: dict[str, Any], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    refresh = credentials.get("refresh_token")
    if not refresh:
        return credentials
    metadata = metadata or {}
    subdomain = metadata.get("subdomain") or credentials.get("subdomain")
    if not subdomain:
        return credentials
    s = _settings()
    with httpx.Client(timeout=30) as client:
        res = client.post(
            f"https://{subdomain}.zendesk.com/oauth/tokens",
            json={
                "grant_type": "refresh_token",
                "refresh_token": refresh,
                "client_id": s.zendesk_client_id,
                "client_secret": s.zendesk_client_secret,
            },
        )
        if res.status_code >= 400:
            return credentials
        data = res.json()
    credentials = dict(credentials)
    credentials["access_token"] = data["access_token"]
    if data.get("refresh_token"):
        credentials["refresh_token"] = data["refresh_token"]
    return credentials


def refresh_gong_token(credentials: dict[str, Any]) -> dict[str, Any]:
    refresh = credentials.get("refresh_token")
    if not refresh:
        return credentials
    s = _settings()
    with httpx.Client(timeout=30) as client:
        res = client.post(
            "https://app.gong.io/oauth2/generate-customer-token",
            auth=(s.gong_client_id, s.gong_client_secret),
            data={
                "grant_type": "refresh_token",
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
    return credentials


def refresh_slack_token(credentials: dict[str, Any]) -> dict[str, Any]:
    refresh = credentials.get("refresh_token")
    if not refresh:
        return credentials
    s = _settings()
    with httpx.Client(timeout=30) as client:
        res = client.post(
            "https://slack.com/api/oauth.v2.access",
            data={
                "grant_type": "refresh_token",
                "client_id": s.slack_client_id,
                "client_secret": s.slack_client_secret,
                "refresh_token": refresh,
            },
        )
        if res.status_code >= 400:
            return credentials
        data = res.json()
    if not data.get("ok"):
        return credentials
    credentials = dict(credentials)
    credentials["access_token"] = data.get("access_token", credentials.get("access_token"))
    if data.get("refresh_token"):
        credentials["refresh_token"] = data["refresh_token"]
    return credentials


def maybe_refresh_credentials(
    provider: str,
    credentials: dict[str, Any],
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Refresh OAuth access tokens when a refresh_token is present."""
    if credentials.get("api_token"):
        return credentials
    refreshers = {
        "hubspot": lambda c: refresh_hubspot_token(c),
        "salesforce": lambda c: refresh_salesforce_token(c, metadata),
        "zendesk": lambda c: refresh_zendesk_token(c, metadata),
        "gong": lambda c: refresh_gong_token(c),
        "ga4": lambda c: refresh_google_token(c),
        "google_drive": lambda c: refresh_google_token(c),
        "slack": lambda c: refresh_slack_token(c),
    }
    refresher = refreshers.get(provider)
    if not refresher:
        return credentials
    return refresher(credentials)
