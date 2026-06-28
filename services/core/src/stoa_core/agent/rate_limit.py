"""Redis rate limits for agent live search and refresh tools."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from stoa_core.config import get_settings
from stoa_core.redis.client import get_redis_sync

logger = logging.getLogger(__name__)


def _hour_bucket() -> str:
    return datetime.now(UTC).strftime("%Y%m%d%H")


def _day_bucket() -> str:
    return datetime.now(UTC).strftime("%Y%m%d")


def check_live_search_limit(org_id: str) -> bool:
    settings = get_settings()
    r = get_redis_sync()
    key = f"stoa:agent:rl:search:{org_id}:{_hour_bucket()}"
    count = int(r.incr(key))
    if count == 1:
        r.expire(key, 3700)
    return count <= settings.agent_live_search_per_org_per_hour


def check_refresh_limit(org_id: str) -> bool:
    settings = get_settings()
    r = get_redis_sync()
    key = f"stoa:agent:rl:refresh:{org_id}:{_hour_bucket()}"
    count = int(r.incr(key))
    if count == 1:
        r.expire(key, 3700)
    return count <= settings.agent_refresh_per_org_per_hour


def check_web_search_limit(org_id: str) -> bool:
    settings = get_settings()
    r = get_redis_sync()
    key = f"stoa:agent:rl:web:{org_id}:{_day_bucket()}"
    count = int(r.incr(key))
    if count == 1:
        r.expire(key, 90000)
    return count <= settings.agent_web_search_per_org_per_day
