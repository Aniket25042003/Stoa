"""Encrypt/decrypt integration credentials at rest."""

from __future__ import annotations

import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from stoa_core.config import get_settings


def _fernet() -> Fernet | None:
    key = get_settings().integration_credentials_key.strip()
    if not key:
        return None
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_credentials(data: dict[str, Any]) -> str:
    f = _fernet()
    payload = json.dumps(data).encode("utf-8")
    if f is None:
        if get_settings().is_production:
            raise RuntimeError("INTEGRATION_CREDENTIALS_KEY is required in production")
        import base64

        return base64.b64encode(payload).decode("ascii")
    return f.encrypt(payload).decode("ascii")


def decrypt_credentials(blob: str | None) -> dict[str, Any]:
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
