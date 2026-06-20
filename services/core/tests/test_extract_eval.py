"""
File: services/core/tests/test_extract_eval.py
Layer: Test Suite
Purpose: Covers regression and behavior checks for test extract eval in the test suite.
Dependencies: stoa_core
"""


from stoa_core.ingestion.extract import extract_signals


def test_extract_returns_list_without_llm():
    """Without LLM keys, extract_signals returns empty list (graceful degradation)."""
    result = extract_signals("Customer complained about slow onboarding and pricing.", "doc-1")
    assert isinstance(result, list)
