"""Async Redis stream reader for SSE endpoints."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

import redis.asyncio as redis_async

from stoa_core.config import get_settings
from stoa_core.redis.client import stream_key


async def read_events_since(
    scope: str,
    entity_id: str,
    last_id: str | None,
    block_ms: int = 15000,
) -> AsyncIterator[tuple[str, dict[str, Any]]]:
    r = redis_async.from_url(get_settings().redis_url, decode_responses=True)
    key = stream_key(scope, entity_id)
    try:
        cur = last_id if last_id is not None else "0-0"
        while True:
            resp = await r.xread({key: cur}, count=50, block=block_ms)
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
