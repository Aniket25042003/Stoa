"""
File: services/core/src/stoa_core/rag/cache.py
Layer: Core Retrieval / RAG
Purpose: Implements cache behavior for the core retrieval / rag.
Dependencies: Redis, stoa_core
"""


from __future__ import annotations

import hashlib
import json
from typing import Any

from stoa_core.config import get_settings
from stoa_core.redis.client import get_redis_sync

KB_VERSION_PREFIX = "stoa:kb:version:"
KB_QUERY_EMB_PREFIX = "stoa:kb:qemb:"
KB_RESULT_PREFIX = "stoa:kb:result:"


def kb_version_key(org_id: str) -> str:
    """Handles kb version key logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    return f"{KB_VERSION_PREFIX}{org_id}"


def bump_kb_version(org_id: str) -> int:
    """Handles bump kb version logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.

    Returns:
        int: Result produced for the caller.
    """
    r = get_redis_sync()
    return int(r.incr(kb_version_key(org_id)))


def get_kb_version(org_id: str) -> int:
    """Handles get kb version logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.

    Returns:
        int: Result produced for the caller.
    """
    r = get_redis_sync()
    val = r.get(kb_version_key(org_id))
    return int(val) if val else 0


def _hash_key(*parts: str) -> str:
    """Handles  hash key logic for the surrounding Stoa workflow.

    Returns:
        str: Result produced for the caller.
    """
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def cache_query_embedding(org_id: str, query: str, embedding: list[float]) -> None:
    """Handles cache query embedding logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.
        query (str): Input value used by this workflow step.
        embedding (list[float]): Input value used by this workflow step.
    """
    settings = get_settings()
    r = get_redis_sync()
    key = f"{KB_QUERY_EMB_PREFIX}{org_id}:{_hash_key(query)}"
    r.setex(key, settings.kb_query_cache_ttl_seconds, json.dumps(embedding))


def get_cached_query_embedding(org_id: str, query: str) -> list[float] | None:
    """Handles get cached query embedding logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.
        query (str): Input value used by this workflow step.

    Returns:
        list[float] | None: Result produced for the caller.
    """
    r = get_redis_sync()
    key = f"{KB_QUERY_EMB_PREFIX}{org_id}:{_hash_key(query)}"
    raw = r.get(key)
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else None
    except json.JSONDecodeError:
        return None


def cache_retrieval_result(
    org_id: str,
    query: str,
    kinds: list[str] | None,
    results: list[dict[str, Any]],
) -> None:
    """Handles cache retrieval result logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.
        query (str): Input value used by this workflow step.
        kinds (list[str] | None): Input value used by this workflow step.
        results (list[dict[str, Any]]): Input value used by this workflow step.
    """
    settings = get_settings()
    r = get_redis_sync()
    version = get_kb_version(org_id)
    kind_key = ",".join(sorted(kinds or []))
    key = f"{KB_RESULT_PREFIX}{org_id}:{version}:{_hash_key(query, kind_key)}"
    r.setex(key, settings.kb_cache_ttl_seconds, json.dumps(results))


def get_cached_retrieval_result(
    org_id: str,
    query: str,
    kinds: list[str] | None,
) -> list[dict[str, Any]] | None:
    """Handles get cached retrieval result logic for the surrounding Stoa workflow.

    Args:
        org_id (str): Input value used by this workflow step.
        query (str): Input value used by this workflow step.
        kinds (list[str] | None): Input value used by this workflow step.

    Returns:
        list[dict[str, Any]] | None: Result produced for the caller.
    """
    r = get_redis_sync()
    version = get_kb_version(org_id)
    kind_key = ",".join(sorted(kinds or []))
    key = f"{KB_RESULT_PREFIX}{org_id}:{version}:{_hash_key(query, kind_key)}"
    raw = r.get(key)
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else None
    except json.JSONDecodeError:
        return None
