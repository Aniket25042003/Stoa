"""
File: services/api/tests/test_redis_security.py
Layer: Test Suite
Purpose: Covers regression and behavior checks for test redis security in the test suite.
Dependencies: Celery, Redis, stoa_core
"""

import pytest

from stoa_core.redis.security import RedisSecurityError, validate_redis_security


def test_api_startup_rejects_insecure_production_redis(monkeypatch):
    monkeypatch.setenv("STOA_ENV", "production")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    from app.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    with pytest.raises(RedisSecurityError):
        validate_redis_security(settings)
    get_settings.cache_clear()


def test_api_startup_rejects_insecure_redis_when_not_development(monkeypatch):
    monkeypatch.setenv("STOA_ENV", "staging")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
    from app.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    assert not settings.is_development
    with pytest.raises(RedisSecurityError):
        validate_redis_security(settings)
    get_settings.cache_clear()
