"""
File: services/core/src/stoa_core/integrations/provider_capabilities.py
Layer: Core Integration Connectors
Purpose: Enriches provider metadata for API clients (connectability, OAuth availability).
"""

from __future__ import annotations

from typing import Any

from stoa_core.config import get_settings
from stoa_core.integrations.base import BaseConnector
from stoa_core.integrations.service import oauth_redirect_uri_for

_OAUTH_ENV_KEYS: dict[str, list[str]] = {
    "hubspot": ["hubspot_client_id", "hubspot_client_secret"],
    "salesforce": ["salesforce_client_id", "salesforce_client_secret"],
    "gong": ["gong_client_id", "gong_client_secret"],
    "zendesk": ["zendesk_client_id", "zendesk_client_secret"],
    "ga4": ["google_client_id", "google_client_secret"],
    "google_drive": ["google_client_id", "google_client_secret"],
    "slack": ["slack_client_id", "slack_client_secret"],
}

_PLATFORM_ENV_KEYS: dict[str, list[str]] = {
    "reddit": ["apify_api_token"],
    "reviews": ["apify_api_token"],
}

_CREDENTIAL_AUTH_PROVIDERS = frozenset(
    {"slack", "zendesk", "gong", "ga4", "google_drive", "intercom", "notion", "jira", "posthog"}
)


def _missing_env(provider: str) -> list[str]:
    settings = get_settings()
    missing: list[str] = []
    for key in _OAUTH_ENV_KEYS.get(provider, []):
        if not str(getattr(settings, key, "") or "").strip():
            missing.append(key.upper())
    for key in _PLATFORM_ENV_KEYS.get(provider, []):
        if not str(getattr(settings, key, "") or "").strip():
            missing.append(key.upper())
    return missing


def oauth_available_for(cls: type[BaseConnector]) -> bool:
    info = cls.provider_info()
    if info.auth_type != "oauth" and not info.supports_credential_auth:
        return False
    if info.auth_type != "oauth":
        return False
    missing = _missing_env(cls.provider)
    if missing:
        return False
    redirect_uri = oauth_redirect_uri_for(cls.provider)
    try:
        url = cls.oauth_authorize_url("probe", redirect_uri)
    except Exception:
        return False
    return bool(url)


def connectable_for(cls: type[BaseConnector]) -> bool:
    info = cls.provider_info()
    if info.connection_mode == "platform":
        return not _missing_env(cls.provider)
    if info.auth_type == "upload":
        return True
    if info.supports_credential_auth:
        return True
    if info.auth_type == "api_key":
        return True
    return oauth_available_for(cls)


def provider_for_api(cls: type[BaseConnector]) -> dict[str, Any]:
    info = cls.provider_info()
    missing = _missing_env(cls.provider)
    oauth_ok = oauth_available_for(cls)
    connectable = connectable_for(cls)
    payload = {
        **info.__dict__,
        "oauth_available": oauth_ok,
        "connectable": connectable,
        "missing_env": missing,
    }
    return payload


def list_providers_for_api() -> list[dict[str, Any]]:
    from stoa_core.integrations.registry import _REGISTRY

    return [provider_for_api(cls) for cls in _REGISTRY.values()]
