"""
File: services/api/app/deps/client_ip.py
Layer: FastAPI Dependencies
Purpose: Implements client ip behavior for the fastapi dependencies.
Dependencies: FastAPI
"""


from __future__ import annotations

from fastapi import Request

from app.config import get_settings


def trusted_client_ip(request: Request) -> str:
    """Resolve the client IP without trusting spoofed X-Forwarded-For from browsers."""
    settings = get_settings()
    proxy_secret = settings.internal_proxy_secret
    if proxy_secret:
        incoming = request.headers.get("x-stoa-proxy-secret", "")
        if incoming == proxy_secret:
            client_ip = request.headers.get("x-stoa-client-ip", "").strip()
            if client_ip:
                return client_ip

    xff = request.headers.get("x-forwarded-for", "")
    if xff and settings.is_production:
        parts = [part.strip() for part in xff.split(",") if part.strip()]
        if parts:
            # The load balancer appends the real client as the rightmost hop.
            return parts[-1]

    if request.client and request.client.host:
        return request.client.host
    return "unknown"
