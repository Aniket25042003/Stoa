import io

import jwt
import pytest
from fastapi.testclient import TestClient

from app.deps.auth import user_id_from_jwt
from app.main import app
from stoa_core.security.sanitize import UploadValidationError, validate_upload

client = TestClient(app)


def test_redact_email():
    from stoa_core.security.pii import redact_pii

    assert "[EMAIL]" in redact_pii("Contact user@example.com today")


def test_celery_task_allowlist():
    from app.services.task_context import ALLOWED_CELERY_TASKS, assert_allowed_task

    assert_allowed_task("ingestion.process_job")
    assert "ingestion.process_job" in ALLOWED_CELERY_TASKS


def test_sanitize_script_tag():
    from stoa_core.security.sanitize import sanitize_user_content

    cleaned = sanitize_user_content("<script>alert(1)</script>")
    assert "<script" not in cleaned.lower() or "[filtered]" in cleaned


def test_validate_upload_rejects_large_file():
    with pytest.raises(UploadValidationError):
        validate_upload("notes.txt", "text/plain", 11 * 1024 * 1024, 10 * 1024 * 1024)


def test_missing_bearer():
    res = client.get("/v1/orgs/me")
    assert res.status_code == 401


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


def test_user_id_from_jwt_rejects_wrong_audience(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-secret")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    from app.config import get_settings

    get_settings.cache_clear()
    token = jwt.encode(
        {"sub": "user-123", "aud": "wrong", "iss": "https://test.supabase.co/auth/v1"},
        "test-secret",
        algorithm="HS256",
    )
    with pytest.raises(Exception):
        user_id_from_jwt(token)
    get_settings.cache_clear()


def test_health_is_public():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
