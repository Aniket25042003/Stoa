"""Redis connection security validation and TLS helpers."""

from __future__ import annotations

import ssl
from dataclasses import dataclass
from urllib.parse import urlparse

from stoa_core.config import Settings, get_settings


class RedisSecurityError(RuntimeError):
    """Raised when Redis is misconfigured for the deployment environment."""


@dataclass(frozen=True)
class RedisConnectionInfo:
    url: str
    scheme: str
    has_password: bool
    uses_tls: bool


def inspect_redis_url(url: str) -> RedisConnectionInfo:
    parsed = urlparse(url)
    scheme = parsed.scheme or "redis"
    return RedisConnectionInfo(
        url=url,
        scheme=scheme,
        has_password=bool(parsed.password),
        uses_tls=scheme == "rediss",
    )


def validate_redis_security(settings: Settings | None = None) -> None:
    """Fail fast when production Redis is reachable without authentication."""
    settings = settings or get_settings()
    info = inspect_redis_url(settings.broker_url)
    if not info.scheme.startswith("redis"):
        raise RedisSecurityError(f"Unsupported Redis scheme: {info.scheme}")

    if settings.is_production:
        if not info.has_password:
            raise RedisSecurityError(
                "Production requires REDIS_URL (or CELERY_BROKER_URL) to include a password"
            )
        if settings.redis_require_tls_effective and not info.uses_tls:
            raise RedisSecurityError(
                "Production requires TLS — use rediss:// in REDIS_URL (set REDIS_REQUIRE_TLS=false to override)"
            )

    backend = inspect_redis_url(settings.result_backend)
    if settings.is_production and not backend.has_password:
        raise RedisSecurityError("Production requires CELERY_RESULT_BACKEND to include a password")


def redis_ssl_kwargs(settings: Settings | None = None) -> dict | None:
    """SSL options for redis-py / Celery when using rediss://."""
    settings = settings or get_settings()
    info = inspect_redis_url(settings.broker_url)
    if not info.uses_tls:
        return None
    cert_reqs = ssl.CERT_REQUIRED if settings.redis_ssl_verify else ssl.CERT_NONE
    return {"ssl_cert_reqs": cert_reqs}


def celery_broker_ssl_config(settings: Settings | None = None) -> dict | None:
    ssl_kwargs = redis_ssl_kwargs(settings)
    if not ssl_kwargs:
        return None
    return {"broker_use_ssl": ssl_kwargs, "redis_backend_use_ssl": ssl_kwargs}
