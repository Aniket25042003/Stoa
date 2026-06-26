"""Tests for KB cache helpers."""

from unittest.mock import MagicMock, patch

from stoa_core.rag.cache import cache_answer, get_cached_answer, get_cached_query_rewrite


@patch("stoa_core.rag.cache.get_redis_sync")
@patch("stoa_core.rag.cache.get_kb_version", return_value=3)
def test_answer_cache_roundtrip(mock_version, mock_redis):
    store: dict[str, str] = {}
    client = MagicMock()

    def _setex(key, ttl, value):
        store[key] = value

    def _get(key):
        return store.get(key)

    client.setex.side_effect = _setex
    client.get.side_effect = _get
    mock_redis.return_value = client

    cache_answer("org-1", "Who was top customer?", ["document"], "Acme Corp")
    cached = get_cached_answer("org-1", "Who was top customer?", ["document"])
    assert cached == "Acme Corp"
    mock_version.assert_called()


@patch("stoa_core.rag.cache.get_redis_sync")
@patch("stoa_core.rag.cache.get_kb_version", return_value=1)
def test_rewrite_cache_miss(mock_version, mock_redis):
    client = MagicMock()
    client.get.return_value = None
    mock_redis.return_value = client
    assert get_cached_query_rewrite("org-1", "short q", "history") is None
