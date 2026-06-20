"""
File: services/core/tests/test_insights.py
Layer: Test Suite
Purpose: Covers regression and behavior checks for test insights in the test suite.
Dependencies: stoa_core
"""

from unittest.mock import patch

from stoa_core.insights.common import COMMON_QUESTIONS, build_executive_summary, precompute_answers


def test_common_questions_count():
    assert len(COMMON_QUESTIONS) == 5


@patch("stoa_core.insights.common.retrieve_context", return_value=[])
def test_precompute_empty_context(mock_retrieve):
    assert precompute_answers("org-1") == []
    mock_retrieve.assert_called()


@patch("stoa_core.insights.common.retrieve_context", return_value=[])
def test_executive_summary_empty(mock_retrieve):
    result = build_executive_summary("org-1", "Acme")
    assert "No customer intelligence" in result["summary"]
