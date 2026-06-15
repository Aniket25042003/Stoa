"""Per-user rate limiting with Redis when available, in-memory fallback."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, status

_lock = Lock()
_buckets: dict[str, list[float]] = defaultdict(list)
_redis_available: bool | None = None

SENSITIVE_SCOPES = frozenset({"auth_signup", "auth_resend", "auth_signin", "waitlist"})


def _memory_check(key: str, limit_per_minute: int) -> None:
    now = time.time()
    window_start = now - 60
    with _lock:
        hits = [t for t in _buckets[key] if t >= window_start]
        if len(hits) >= limit_per_minute:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Rate limit exceeded")
        hits.append(now)
        _buckets[key] = hits[-limit_per_minute:]


def _redis_check(key: str, limit_per_minute: int) -> None:
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


def _fail_closed_for_scope(scope: str) -> bool:
    return scope in SENSITIVE_SCOPES or scope.endswith(":email")


def check_rate_limit(user_id: str, limit_per_minute: int = 60, *, scope: str = "default") -> None:
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
