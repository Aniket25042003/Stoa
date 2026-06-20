"""
File: services/core/src/stoa_core/redis/security.py
Layer: Core Redis Infrastructure
Purpose: Implements security behavior for the core redis infrastructure.
Dependencies: Celery, Redis, stoa_core
"""


from __future__ import annotations

import ssl
from dataclasses import dataclass
from urllib.parse import urlparse

from stoa_core.config import Settings, get_settings


class RedisSecurityError(RuntimeError):
    """Raised when Redis is misconfigured for the deployment environment."""


@dataclass(frozen=True)
class RedisConnectionInfo:
    """Manage RedisConnectionInfo behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    url: str
    scheme: str
    has_password: bool
    uses_tls: bool


def inspect_redis_url(url: str) -> RedisConnectionInfo:
    """Handles inspect redis url logic for the surrounding Stoa workflow.

    Args:
        url (str): Input value used by this workflow step.

    Returns:
        RedisConnectionInfo: Result produced for the caller.
    """
    parsed = urlparse(url)
    scheme = parsed.scheme or "redis"
    return RedisConnectionInfo(
        url=url,
        scheme=scheme,
        has_password=bool(parsed.password),
        uses_tls=scheme == "rediss",
    )


def is_render_internal_keyvalue(url: str) -> bool:
    """Render private-network Key Value URLs use redis://red-<id>:6379 without auth."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "redis" and host.startswith("red-")


def _localhost_default(url: str) -> bool:
    """Handles  localhost default logic for the surrounding Stoa workflow.

    Args:
        url (str): Input value used by this workflow step.

    Returns:
        bool: Result produced for the caller.
    """
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return host in {"localhost", "127.0.0.1", "::1"}


def validate_redis_security(settings: Settings | None = None) -> None:
    """Fail fast when production Redis is reachable without authentication."""
    settings = settings or get_settings()
    info = inspect_redis_url(settings.broker_url)
    if not info.scheme.startswith("redis"):
        raise RedisSecurityError(f"Unsupported Redis scheme: {info.scheme}")

    if not settings.is_development:
        render_internal = is_render_internal_keyvalue(settings.broker_url)
        if _localhost_default(settings.broker_url):
            raise RedisSecurityError(
                "REDIS_URL is not configured for production — link the stoa-redis "
                "Key Value instance on Render (or set REDIS_URL to a rediss:// URL "
                "with a password)"
            )
        if not info.has_password and not render_internal:
            raise RedisSecurityError(
                "Redis URL must include a password "
                "(set STOA_ENV=development for local-only override)"
            )
        if settings.redis_require_tls_effective and not info.uses_tls and not render_internal:
            raise RedisSecurityError(
                "TLS required — use rediss:// in REDIS_URL "
                "(set REDIS_REQUIRE_TLS=false to override)"
            )

    backend = inspect_redis_url(settings.result_backend)
    if not settings.is_development:
        if _localhost_default(settings.result_backend):
            raise RedisSecurityError("CELERY_RESULT_BACKEND is not configured for production")
        if not backend.has_password and not is_render_internal_keyvalue(settings.result_backend):
            raise RedisSecurityError("CELERY_RESULT_BACKEND must include a password")


def redis_ssl_kwargs(settings: Settings | None = None) -> dict | None:
    """SSL options for redis-py / Celery when using rediss://."""
    settings = settings or get_settings()
    info = inspect_redis_url(settings.broker_url)
    if not info.uses_tls:
        return None
    cert_reqs = ssl.CERT_REQUIRED if settings.redis_ssl_verify else ssl.CERT_NONE
    return {"ssl_cert_reqs": cert_reqs}


def celery_broker_ssl_config(settings: Settings | None = None) -> dict | None:
    """Handles celery broker ssl config logic for the surrounding Stoa workflow.

    Args:
        settings (Settings | None): Input value used by this workflow step.

    Returns:
        dict | None: Result produced for the caller.
    """
    ssl_kwargs = redis_ssl_kwargs(settings)
    if not ssl_kwargs:
        return None
    return {"broker_use_ssl": ssl_kwargs, "redis_backend_use_ssl": ssl_kwargs}
