from __future__ import annotations

from unittest.mock import patch

from stoa_core.research.serp import research_competitors


@patch("stoa_core.research.serp.get_settings")
def test_research_competitors_without_key(mock_settings):
    mock_settings.return_value.serpapi_api_key = ""
    result = research_competitors("Acme competitors")
    assert not result.items
    assert result.warnings
