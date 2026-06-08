from __future__ import annotations

import json
import time
from typing import Any

import redis

from app.config import get_settings

STREAM_MAXLEN = 10_000
TTL = 72 * 3600


def _client() -> redis.Redis:
    s = get_settings()
    return redis.from_url(s.redis_url, decode_responses=True)


def publish_event_sync(run_id: str, payload: dict[str, Any]) -> None:
    key = f"gtm:run:{run_id}:events"
    r = _client()
    try:
        body = json.dumps({"ts": time.time(), **payload})
        r.xadd(key, {"data": body}, maxlen=STREAM_MAXLEN, approximate=True)
        r.expire(key, TTL)
    finally:
        r.close()


def read_events_blocking(run_id: str, last_id: str, block_ms: int = 5000) -> list[tuple[str, dict[str, Any]]]:
    key = f"gtm:run:{run_id}:events"
    r = _client()
    try:
        resp = r.xread({key: last_id}, count=50, block=block_ms)
        out: list[tuple[str, dict[str, Any]]] = []
        if not resp:
            return out
        for _name, messages in resp:
            for msg_id, fields in messages:
                raw = fields.get("data") or "{}"
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    data = {"message": raw}
                out.append((str(msg_id), data))
        return out
    finally:
        r.close()
