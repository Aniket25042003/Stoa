"""
File: services/core/src/stoa_core/redis/sse.py
Layer: Core Redis Infrastructure
Purpose: Implements sse behavior for the core redis infrastructure.
Dependencies: Redis, stoa_core
"""


from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import redis.asyncio as redis_async

from stoa_core.config import get_settings
from stoa_core.redis.client import stream_key

_SSE_WAIT_MESSAGES = (
    "Reviewing your workspace…",
    "Cross-checking customer signals…",
    "Pulling patterns from your data…",
    "Connecting insights across sources…",
    "Looking for what matters most…",
)
_wait_message_index = 0


async def read_events_since(
    scope: str,
    entity_id: str,
    last_id: str | None,
    block_ms: int = 15000,
) -> AsyncIterator[tuple[str, dict[str, Any]]]:
    """Asynchronously handles read events since logic for the surrounding Stoa workflow.

    Args:
        scope (str): Input value used by this workflow step.
        entity_id (str): Input value used by this workflow step.
        last_id (str | None): Input value used by this workflow step.
        block_ms (int): Input value used by this workflow step.

    Returns:
        AsyncIterator[tuple[str, dict[str, Any]]]: Result produced for the caller.
    """
    r = redis_async.from_url(get_settings().redis_url, decode_responses=True)
    key = stream_key(scope, entity_id)
    try:
        cur = last_id if last_id is not None else "0-0"
        while True:
            resp = await r.xread({key: cur}, count=50, block=block_ms)
            if not resp:
                global _wait_message_index
                message = _SSE_WAIT_MESSAGES[_wait_message_index % len(_SSE_WAIT_MESSAGES)]
                _wait_message_index += 1
                yield ("heartbeat", {"status": "thinking", "message": message})
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
