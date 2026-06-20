"""
File: services/api/tests/test_rate_limit.py
Layer: Test Suite
Purpose: Covers regression and behavior checks for test rate limit in the test suite.
Dependencies: FastAPI, Redis
"""

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.deps.client_ip import trusted_client_ip
from app.deps.rate_limit import SENSITIVE_SCOPES, check_public_rate_limit, check_rate_limit


def _request(headers: dict[str, str] | None = None, client_host: str = "203.0.113.10") -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        "client": (client_host, 0),
    }
    return Request(scope)


def test_trusted_client_ip_ignores_spoofed_xff_without_proxy_secret(monkeypatch):
    monkeypatch.setenv("STOA_ENV", "development")
    from app.config import get_settings

    get_settings.cache_clear()
    request = _request({"x-forwarded-for": "1.2.3.4, 198.51.100.2"})
    assert trusted_client_ip(request) == "203.0.113.10"
    get_settings.cache_clear()


def test_trusted_client_ip_uses_proxy_headers_when_secret_matches(monkeypatch):
    monkeypatch.setenv("STOA_ENV", "development")
    monkeypatch.setenv("INTERNAL_PROXY_SECRET", "proxy-test-secret")
    from app.config import get_settings

    get_settings.cache_clear()
    request = _request(
        {
            "x-stoa-proxy-secret": "proxy-test-secret",
            "x-stoa-client-ip": "198.51.100.44",
            "x-forwarded-for": "1.2.3.4",
        }
    )
    assert trusted_client_ip(request) == "198.51.100.44"
    get_settings.cache_clear()


def test_sensitive_scope_fails_closed_without_redis(monkeypatch):
    monkeypatch.setattr("app.deps.rate_limit._use_redis", lambda: False)
    with pytest.raises(HTTPException) as exc:
        check_rate_limit("203.0.113.1", 5, scope="auth_signup")
    assert exc.value.status_code == 503
    assert "auth_signup" in SENSITIVE_SCOPES


def test_public_rate_limit_applies_email_scope(monkeypatch):
    monkeypatch.setattr("app.deps.rate_limit._use_redis", lambda: False)
    with pytest.raises(HTTPException):
        check_public_rate_limit("203.0.113.1", email="user@example.com", scope="auth_signup")
