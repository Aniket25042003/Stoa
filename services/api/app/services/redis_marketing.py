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
