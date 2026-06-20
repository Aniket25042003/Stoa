"""
File: services/api/tests/test_competitive_competitors.py
Layer: Test Suite
Purpose: Covers regression and behavior checks for test competitive competitors in the test suite.
Dependencies: FastAPI, Supabase
"""


from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.routers.competitive import _get_competitor_for_org, _validate_competitor_urls


def test_get_competitor_for_org_returns_row() -> None:
    competitor = {"id": "comp-1", "org_id": "org-1", "name": "Acme"}
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
        data=[competitor]
    )
    with patch("app.routers.competitive.get_supabase_admin", return_value=sb):
        assert _get_competitor_for_org("org-1", "comp-1") == competitor


def test_validate_competitor_urls_rejects_unsafe_url() -> None:
    with patch("app.routers.competitive.assert_safe_fetch_url", side_effect=ValueError("blocked")):
        with pytest.raises(HTTPException) as exc:
            _validate_competitor_urls("http://localhost")
    assert exc.value.status_code == 400
