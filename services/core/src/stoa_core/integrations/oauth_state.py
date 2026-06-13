"""OAuth state storage in Redis."""

from __future__ import annotations

import json
import secrets
import time
from typing import Any

from stoa_core.redis.client import get_redis_sync

OAUTH_STATE_TTL = 600


def create_oauth_state(org_id: str, user_id: str, provider: str, extra: dict[str, Any] | None = None) -> str:
    state = secrets.token_urlsafe(32)
    payload = {
        "org_id": org_id,
        "user_id": user_id,
        "provider": provider,
        "created_at": time.time(),
        **(extra or {}),
    }
    r = get_redis_sync()
    r.setex(f"stoa:oauth:state:{state}", OAUTH_STATE_TTL, json.dumps(payload))
    return state


def consume_oauth_state(state: str) -> dict[str, Any] | None:
    r = get_redis_sync()
    key = f"stoa:oauth:state:{state}"
    raw = r.get(key)
    if not raw:
        return None
    r.delete(key)
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None
