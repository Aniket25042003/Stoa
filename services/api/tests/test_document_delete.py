"""
File: services/api/tests/test_document_delete.py
Layer: Test Suite
Purpose: Covers regression and behavior checks for test document delete in the test suite.
Dependencies: Supabase
"""


from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.document_ingestion import (
    delete_document_for_org,
    get_document_for_org,
    is_pasted_document,
    update_pasted_document_for_org,
)


def test_get_document_for_org_returns_row() -> None:
    doc = {"id": "doc-1", "org_id": "org-1", "title": "Test"}
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[doc]
    )
    with patch("app.services.document_ingestion.get_supabase_admin", return_value=sb):
        assert get_document_for_org("org-1", "doc-1") == doc


def test_is_pasted_document() -> None:
    assert is_pasted_document({"storage_path": None})
    assert is_pasted_document({})
    assert not is_pasted_document({"storage_path": "org/doc/file.txt"})


def test_update_pasted_document_rejects_uploads() -> None:
    with patch(
        "app.services.document_ingestion.get_document_for_org",
        return_value={"id": "doc-1", "storage_path": "org/doc/file.txt"},
    ):
        with pytest.raises(ValueError, match="Uploaded files cannot be edited"):
            update_pasted_document_for_org("org-1", "doc-1", "user-1", content="new text")


def test_delete_document_for_org_removes_related_records() -> None:
    doc = {
        "id": "doc-1",
        "org_id": "org-1",
        "title": "Test",
        "storage_path": "org-1/doc-1/file.txt",
    }
    sb = MagicMock()
    with patch("app.services.document_ingestion.get_document_for_org", return_value=doc):
        with patch("app.services.document_ingestion.get_supabase_admin", return_value=sb):
            with patch("app.services.document_ingestion.get_settings") as settings:
                settings.return_value.storage_bucket = "intelligence-documents"
                assert delete_document_for_org("org-1", "doc-1") is True
    sb.storage.from_.return_value.remove.assert_called_once_with(["org-1/doc-1/file.txt"])
    assert sb.table.return_value.delete.call_count == 4
