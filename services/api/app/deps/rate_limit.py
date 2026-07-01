"""
File: services/api/app/deps/rate_limit.py
Layer: FastAPI Dependencies
Purpose: Implements rate limit behavior for the fastapi dependencies.
Dependencies: FastAPI, Redis, stoa_core
"""


from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, status

_lock = Lock()
_buckets: dict[str, list[float]] = defaultdict(list)
_redis_available: bool | None = None

SENSITIVE_SCOPES = frozenset({"auth_signup", "auth_resend", "auth_signin", "waitlist", "hubspot_webhook"})
EXPENSIVE_SCOPES = frozenset(
    {
        "ask",
        "campaign_create",
        "competitor_add",
        "competitor_delete",
        "competitor_scan",
        "competitor_update",
        "content_generation",
        "document_update",
        "icp_rebuild",
        "insights_refresh",
        "campaign_analysis_refresh",
        "alignment_refresh",
        "integrations",
        "paste",
        "upload",
        "integration_resources",
        "team_invite",
        "org_create",
        "csv_detect",
        "conversation_delete",
    }
)


def _memory_check(key: str, limit_per_minute: int) -> None:
    """Handles  memory check logic for the surrounding Stoa workflow.

    Args:
        key (str): Input value used by this workflow step.
        limit_per_minute (int): Input value used by this workflow step.
    """
    now = time.time()
    window_start = now - 60
    with _lock:
        hits = [t for t in _buckets[key] if t >= window_start]
        if len(hits) >= limit_per_minute:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Rate limit exceeded")
        hits.append(now)
        _buckets[key] = hits[-limit_per_minute:]


def _redis_check(key: str, limit_per_minute: int) -> None:
    """Handles  redis check logic for the surrounding Stoa workflow.

    Args:
        key (str): Input value used by this workflow step.
        limit_per_minute (int): Input value used by this workflow step.
    """
    from stoa_core.redis.client import get_redis_sync

    r = get_redis_sync()
    now = int(time.time())
    window_key = f"stoa:ratelimit:{key}:{now // 60}"
    count = int(r.incr(window_key))
    if count == 1:
        r.expire(window_key, 120)
    if count > limit_per_minute:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Rate limit exceeded")


def _use_redis() -> bool:
    """Handles  use redis logic for the surrounding Stoa workflow.

    Returns:
        bool: Result produced for the caller.
    """
    global _redis_available
    if _redis_available is not None:
        return _redis_available
    try:
        from stoa_core.redis.client import get_redis_sync

        get_redis_sync().ping()
        _redis_available = True
    except Exception:
        _redis_available = False
    return _redis_available


def _is_development() -> bool:
    from stoa_core.config import get_settings

    return get_settings().is_development


def _fail_closed_for_scope(scope: str) -> bool:
    """Handles  fail closed for scope logic for the surrounding Stoa workflow.

    Args:
        scope (str): Input value used by this workflow step.

    Returns:
        bool: Result produced for the caller.
    """
    if scope.endswith(":email"):
        return True
    if scope in SENSITIVE_SCOPES:
        return True
    if scope in EXPENSIVE_SCOPES:
        return True
    return False


def check_rate_limit(user_id: str, limit_per_minute: int = 60, *, scope: str = "default") -> None:
    """Handles check rate limit logic for the surrounding Stoa workflow.

    Args:
        user_id (str): Input value used by this workflow step.
        limit_per_minute (int): Input value used by this workflow step.
        scope (str): Input value used by this workflow step.
    """
    key = f"{scope}:{user_id}"
    fail_closed = _fail_closed_for_scope(scope)
    if _use_redis():
        try:
            _redis_check(key, limit_per_minute)
            return
        except HTTPException:
            raise
        except Exception:
            if fail_closed:
                raise HTTPException(
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                    "Rate limiting temporarily unavailable",
                ) from None
    elif fail_closed:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Rate limiting temporarily unavailable",
        )
    _memory_check(key, limit_per_minute)


def check_public_rate_limit(
    client_ip: str,
    *,
    email: str | None = None,
    ip_limit_per_minute: int = 5,
    email_limit_per_minute: int = 3,
    scope: str,
) -> None:
    """Rate limit public endpoints by trusted IP and optional email."""
    check_rate_limit(client_ip or "unknown", ip_limit_per_minute, scope=scope)
    if email:
        check_rate_limit(email.strip().lower(), email_limit_per_minute, scope=f"{scope}:email")
