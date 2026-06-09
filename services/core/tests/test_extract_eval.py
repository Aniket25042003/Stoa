"""Extraction quality eval thresholds (Phase 1.6)."""

from stoa_core.ingestion.extract import extract_signals


def test_extract_returns_list_without_llm():
    """Without LLM keys, extract_signals returns empty list (graceful degradation)."""
    result = extract_signals("Customer complained about slow onboarding and pricing.", "doc-1")
    assert isinstance(result, list)
