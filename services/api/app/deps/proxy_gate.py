"""
File: services/api/app/deps/proxy_gate.py
Layer: FastAPI Dependencies
Purpose: Require BFF proxy secret on non-public routes outside local development.
"""

from __future__ import annotations

import secrets

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings

_PUBLIC_PATHS = frozenset({"/health"})


def _is_public_path(path: str) -> bool:
    if path in _PUBLIC_PATHS:
        return True
    if path.startswith("/v1/integrations/callback/"):
        return True
    if path.startswith("/v1/integrations/webhooks/"):
        return True
    return False


class ProxySecretMiddleware(BaseHTTPMiddleware):
    """Reject direct API access without the internal proxy secret (non-dev only)."""

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if settings.is_development or request.method == "OPTIONS":
            return await call_next(request)
        if _is_public_path(request.url.path):
            return await call_next(request)

        secret = settings.internal_proxy_secret.strip()
        if not secret:
            return JSONResponse(
                status_code=503,
                content={"detail": "INTERNAL_PROXY_SECRET is not configured"},
            )

        incoming = request.headers.get("x-stoa-proxy-secret", "")
        if not secrets.compare_digest(incoming, secret):
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})

        return await call_next(request)
