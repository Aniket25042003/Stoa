"""Sync Redis client for workers and event publishing."""

from __future__ import annotations

import json
import time
from functools import lru_cache
from typing import Any

import redis

from stoa_core.config import get_settings
from stoa_core.redis.security import redis_ssl_kwargs, validate_redis_security
from stoa_core.security.pii import redact_json

STREAM_MAXLEN = 10_000
STREAM_TTL_SEC = 72 * 3600


def stream_key(scope: str, entity_id: str) -> str:
    return f"stoa:{scope}:{entity_id}:events"


@lru_cache
def get_redis_sync() -> redis.Redis:
    settings = get_settings()
    validate_redis_security(settings)
    ssl_kwargs = redis_ssl_kwargs(settings) or {}
    return redis.from_url(settings.redis_url, decode_responses=True, **ssl_kwargs)


def publish_event(scope: str, entity_id: str, payload: dict[str, Any]) -> str:
    r = get_redis_sync()
    key = stream_key(scope, entity_id)
    safe_payload = redact_json({"ts": time.time(), **payload})
    body = json.dumps(safe_payload)
    msg_id = r.xadd(key, {"data": body}, maxlen=STREAM_MAXLEN, approximate=True)
    r.expire(key, STREAM_TTL_SEC)
    return str(msg_id)
