"""
File: services/api/tests/test_task_context.py
Layer: Test Suite
Purpose: Covers regression and behavior checks for test task context in the test suite.
Dependencies: Supabase, Celery
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.services.task_context import (
    ALLOWED_CELERY_TASKS,
    assert_allowed_task,
    verify_ingestion_job,
)


def test_allowed_task_registry():
    assert "ingestion.process_job" in ALLOWED_CELERY_TASKS
    assert "evil.task" not in ALLOWED_CELERY_TASKS


def test_assert_allowed_task_rejects_unknown():
    with pytest.raises(ValueError, match="Disallowed"):
        assert_allowed_task("malicious.inject")


@patch("app.services.task_context.get_supabase_admin")
def test_verify_ingestion_job_org_mismatch(mock_admin):
    job_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    org_a = str(uuid.uuid4())
    org_b = str(uuid.uuid4())

    sb = MagicMock()
    mock_admin.return_value = sb
    sb.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.side_effect = [
        MagicMock(data=[{"id": job_id, "org_id": org_a, "document_id": doc_id, "status": "queued"}]),
        MagicMock(data=[{"id": doc_id, "org_id": org_b, "content": "x", "title": "t", "doc_type": "note"}]),
    ]

    with pytest.raises(ValueError, match="org mismatch"):
        verify_ingestion_job(job_id)
