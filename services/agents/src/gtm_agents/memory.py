from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

MEMORY_TTL_SECONDS = 72 * 3600


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _memory_key(run_id: str) -> str:
    return f"gtm:run:{run_id}:memory"


def _snapshot_key(run_id: str) -> str:
    return f"gtm:run:{run_id}:ctx"


def _client():
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return None
    try:
        import redis

        return redis.from_url(redis_url, decode_responses=True)
    except Exception:
        return None


def append_memory(run_id: str | None, agent: str, kind: str, payload: dict[str, Any]) -> None:
    if not run_id:
        return
    client = _client()
    if client is None:
        return
    record = {"ts": _now(), "agent": agent, "kind": kind, "payload": payload}
    try:
        client.rpush(_memory_key(run_id), json.dumps(record, default=str))
        client.ltrim(_memory_key(run_id), -500, -1)
        client.expire(_memory_key(run_id), MEMORY_TTL_SECONDS)
    finally:
        client.close()


def read_memory(run_id: str | None, limit: int = 50) -> list[dict[str, Any]]:
    if not run_id:
        return []
    client = _client()
    if client is None:
        return []
    try:
        raw = client.lrange(_memory_key(run_id), max(0, -limit), -1)
        out = []
        for item in raw:
            try:
                parsed = json.loads(item)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                out.append(parsed)
        return out
    finally:
        client.close()


def write_context_snapshot(run_id: str | None, payload: dict[str, Any]) -> None:
    if not run_id:
        return
    client = _client()
    if client is None:
        return
    try:
        client.setex(_snapshot_key(run_id), MEMORY_TTL_SECONDS, json.dumps(payload, default=str))
    finally:
        client.close()
