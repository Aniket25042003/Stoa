import pytest

from stoa_core.config import Settings
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
