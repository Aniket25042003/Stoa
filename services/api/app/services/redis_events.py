from __future__ import annotations

import json
import time
from typing import Any, AsyncIterator

import redis.asyncio as redis

from app.config import get_settings

STREAM_MAXLEN = 10_000
CTX_TTL_SEC = 72 * 3600


def stream_key(run_id: str) -> str:
    return f"gtm:run:{run_id}:events"


def ctx_key(run_id: str) -> str:
    return f"gtm:run:{run_id}:ctx"


async def get_redis() -> redis.Redis:
    s = get_settings()
    return redis.from_url(s.redis_url, decode_responses=True)


async def publish_event(run_id: str, payload: dict[str, Any]) -> str:
    r = await get_redis()
    try:
        body = json.dumps({"ts": time.time(), **payload})
        msg_id = await r.xadd(
            stream_key(run_id),
            {"data": body},
            maxlen=STREAM_MAXLEN,
            approximate=True,
        )
        await r.expire(stream_key(run_id), CTX_TTL_SEC)
        return str(msg_id)
    finally:
        await r.aclose()


async def read_events_since(
    run_id: str, last_id: str | None, block_ms: int = 15000
) -> AsyncIterator[tuple[str, dict[str, Any]]]:
    """Async generator yielding (stream_id, parsed_payload) from Redis Stream."""
    r = await get_redis()
    try:
        # "$" = only messages arriving after XREAD starts (no history replay)
        cur = last_id if last_id is not None else "0-0"
        while True:
            resp = await r.xread({stream_key(run_id): cur}, count=50, block=block_ms)
            if not resp:
                yield ("heartbeat", {"message": "keepalive"})
                continue
            for _name, messages in resp:
                for msg_id, fields in messages:
                    cur = msg_id
                    raw = fields.get("data") or "{}"
                    try:
                        data = json.loads(raw)
                    except json.JSONDecodeError:
                        data = {"message": raw}
                    yield (str(msg_id), data)
    finally:
        await r.aclose()
