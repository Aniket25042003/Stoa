"""
File: services/core/src/stoa_core/integrations/crypto.py
Layer: Core Integration Connectors
Purpose: Implements crypto behavior for the core integration connectors.
Dependencies: stoa_core
"""


from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken

from stoa_core.config import get_settings


def _integrations_require_encryption() -> bool:
    """True when the API is not running on localhost (integrations outside local dev)."""
    settings = get_settings()
    if settings.is_development:
        return False
    host = (urlparse(settings.api_base_url).hostname or "").lower()
    return host not in {"localhost", "127.0.0.1", "::1"}


def _fernet() -> Fernet | None:
    """Handles  fernet logic for the surrounding Stoa workflow.

    Returns:
        Fernet | None: Result produced for the caller.
    """
    key = get_settings().integration_credentials_key.strip()
    if not key:
        return None
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_credentials(data: dict[str, Any]) -> str:
    """Handles encrypt credentials logic for the surrounding Stoa workflow.

    Args:
        data (dict[str, Any]): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    f = _fernet()
    payload = json.dumps(data).encode("utf-8")
    if f is None:
        if get_settings().is_production or _integrations_require_encryption():
            raise RuntimeError(
                "INTEGRATION_CREDENTIALS_KEY is required when integrations are used outside local development"
            )
        import base64

        return base64.b64encode(payload).decode("ascii")
    return f.encrypt(payload).decode("ascii")


def decrypt_credentials(blob: str | None) -> dict[str, Any]:
    """Handles decrypt credentials logic for the surrounding Stoa workflow.

    Args:
        blob (str | None): Input value used by this workflow step.

    Returns:
        dict[str, Any]: Result produced for the caller.
    """
    if not blob:
        return {}
    f = _fernet()
    try:
        if f is None:
            import base64

            raw = base64.b64decode(blob.encode("ascii"))
        else:
            raw = f.decrypt(blob.encode("ascii"))
        parsed = json.loads(raw.decode("utf-8"))
        return parsed if isinstance(parsed, dict) else {}
    except (InvalidToken, json.JSONDecodeError, ValueError):
        return {}
