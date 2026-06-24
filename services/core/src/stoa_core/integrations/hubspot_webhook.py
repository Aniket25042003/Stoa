"""
File: services/core/src/stoa_core/integrations/hubspot_webhook.py
Layer: Core Integration Connectors
Purpose: Validate HubSpot webhook request signatures (v3).
Dependencies: stoa_core
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
from typing import Final

_MAX_TIMESTAMP_SKEW_SECONDS: Final[int] = 300


def compute_hubspot_signature_v3(
    *,
    client_secret: str,
    method: str,
    request_uri: str,
    body: bytes,
    timestamp: str,
) -> str:
    """HubSpot v3: base64(HMAC-SHA256(secret, method + uri + body + timestamp))."""
    source = f"{method}{request_uri}{body.decode('utf-8')}{timestamp}"
    digest = hmac.new(client_secret.encode("utf-8"), source.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def verify_hubspot_signature_v3(
    *,
    client_secret: str,
    method: str,
    request_uri: str,
    body: bytes,
    signature: str | None,
    timestamp: str | None,
) -> bool:
    """Return True when the HubSpot v3 signature and timestamp are valid."""
    if not client_secret or not signature or not timestamp:
        return False
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False
    if abs(time.time() - ts) > _MAX_TIMESTAMP_SKEW_SECONDS:
        return False
    expected = compute_hubspot_signature_v3(
        client_secret=client_secret,
        method=method.upper(),
        request_uri=request_uri,
        body=body,
        timestamp=timestamp,
    )
    return hmac.compare_digest(expected, signature)


def hubspot_portal_matches_metadata(portal_id: str, provider_metadata: dict | None) -> bool:
    """Match webhook portalId to stored HubSpot hub metadata."""
    if not portal_id:
        return False
    meta = provider_metadata or {}
    stored = meta.get("hub_id") or meta.get("portalId") or meta.get("portal_id")
    return stored is not None and str(stored) == str(portal_id)
