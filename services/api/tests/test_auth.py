import jwt
import pytest

from app.deps.auth import user_id_from_jwt


def test_user_id_from_jwt_hs256(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-secret")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    from app.config import get_settings

    get_settings.cache_clear()
    token = jwt.encode(
        {"sub": "user-123", "aud": "authenticated", "iss": "https://test.supabase.co/auth/v1"},
        "test-secret",
        algorithm="HS256",
    )
    assert user_id_from_jwt(token) == "user-123"
    get_settings.cache_clear()


def test_user_id_from_jwt_rejects_invalid_audience(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-secret")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    from app.config import get_settings

    get_settings.cache_clear()
    token = jwt.encode(
        {"sub": "user-123", "aud": "service_role", "iss": "https://test.supabase.co/auth/v1"},
        "test-secret",
        algorithm="HS256",
    )
    with pytest.raises(Exception):
        user_id_from_jwt(token)
    get_settings.cache_clear()
