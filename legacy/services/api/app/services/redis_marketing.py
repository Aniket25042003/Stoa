from __future__ import annotations

import json
import time
from typing import Any

import redis

from app.config import get_settings
from app.services.redis_events import mkt_stream_key

STREAM_MAXLEN = 10_000
TTL = 72 * 3600


def _client() -> redis.Redis:
    s = get_settings()
    return redis.from_url(s.redis_url, decode_responses=True)


def publish_marketing_event_sync(chat_id: str, payload: dict[str, Any]) -> None:
    key = mkt_stream_key(chat_id)
    r = _client()
    try:
        body = json.dumps({"ts": time.time(), **payload})
        r.xadd(key, {"data": body}, maxlen=STREAM_MAXLEN, approximate=True)
        r.expire(key, TTL)
    finally:
        r.close()


def marketing_turn_lock_key(chat_id: str, message_id: str) -> str:
    return f"mkt:chat:{chat_id}:turn:{message_id}"


def try_acquire_marketing_turn_lock(chat_id: str, message_id: str, *, ttl_sec: int = 3600) -> bool:
    """Return True if this worker owns the turn (SET NX). False if another worker already runs it."""
    r = _client()
    try:
        return bool(r.set(marketing_turn_lock_key(chat_id, message_id), "1", nx=True, ex=ttl_sec))
    finally:
        r.close()


def release_marketing_turn_lock(chat_id: str, message_id: str) -> None:
    """Call on failure so Celery retry can re-run the turn."""
    r = _client()
    try:
        r.delete(marketing_turn_lock_key(chat_id, message_id))
    finally:
        r.close()
