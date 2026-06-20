"""
File: services/core/tests/test_redis_security.py
Layer: Test Suite
Purpose: Covers regression and behavior checks for test redis security in the test suite.
Dependencies: Celery, Redis, stoa_core
"""

import pytest

from stoa_core.config import Settings
from stoa_core.redis.security import RedisSecurityError, inspect_redis_url, validate_redis_security


def test_inspect_redis_url_detects_password_and_tls():
    info = inspect_redis_url("rediss://:secret@redis.example.com:6379/0")
    assert info.has_password is True
    assert info.uses_tls is True


def test_production_requires_password():
    settings = Settings(
        stoa_env="production",
        redis_url="redis://public.example.com:6379/0",
        celery_broker_url="",
        celery_result_backend="",
    )
    with pytest.raises(RedisSecurityError, match="password"):
        validate_redis_security(settings)


def test_production_requires_tls_by_default():
    settings = Settings(
        stoa_env="production",
        redis_url="redis://:secret@redis.example.com:6379/0",
        celery_broker_url="",
        celery_result_backend="",
    )
    with pytest.raises(RedisSecurityError, match="TLS"):
        validate_redis_security(settings)


def test_production_accepts_rediss_with_password():
    settings = Settings(
        stoa_env="production",
        redis_url="rediss://:secret@redis.example.com:6379/0",
        celery_broker_url="",
        celery_result_backend="",
    )
    validate_redis_security(settings)


def test_production_accepts_render_internal_keyvalue():
    settings = Settings(
        stoa_env="production",
        redis_url="redis://red-abc123xyz:6379",
        celery_broker_url="redis://red-abc123xyz:6379",
        celery_result_backend="redis://red-abc123xyz:6379",
        redis_require_tls=True,
    )
    validate_redis_security(settings)


def test_production_rejects_unconfigured_localhost_default():
    settings = Settings(
        stoa_env="production",
        redis_url="redis://localhost:6379/0",
        celery_broker_url="",
        celery_result_backend="",
    )
    with pytest.raises(RedisSecurityError, match="not configured"):
        validate_redis_security(settings)


def test_development_allows_unauthenticated_local():
    settings = Settings(
        stoa_env="development",
        redis_url="redis://localhost:6379/0",
        celery_broker_url="",
        celery_result_backend="",
    )
    validate_redis_security(settings)


def test_unset_stoa_env_with_localhost_redis_is_development():
    settings = Settings(
        stoa_env="",
        redis_url="redis://:localdev@localhost:6379/0",
        celery_broker_url="",
        celery_result_backend="",
    )
    assert settings.is_development is True
    validate_redis_security(settings)


def test_unset_stoa_env_with_remote_redis_stays_strict():
    settings = Settings(
        stoa_env="",
        redis_url="redis://public.example.com:6379/0",
        celery_broker_url="",
        celery_result_backend="",
    )
    assert settings.is_development is False
    with pytest.raises(RedisSecurityError, match="password"):
        validate_redis_security(settings)
