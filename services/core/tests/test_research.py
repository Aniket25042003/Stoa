from __future__ import annotations

from unittest.mock import MagicMock, patch

from stoa_core.research.fetch import html_to_text
from stoa_core.research.types import ResearchItem
from stoa_core.research.web import _dedupe, research_web


def test_html_to_text_strips_tags():
    html = "<html><body><h1>Acme</h1><p>We build <b>software</b>.</p></body></html>"
    text = html_to_text(html)
    assert "Acme" in text
    assert "software" in text
    assert "<" not in text


def test_dedupe_research_items():
    items = [
        ResearchItem(
            source_type="web",
            title="A",
            raw_excerpt="x",
            summary="x",
            source_url="https://a.com",
        ),
        ResearchItem(
            source_type="web",
            title="A",
            raw_excerpt="x",
            summary="x",
            source_url="https://a.com",
        ),
    ]
    assert len(_dedupe(items)) == 1


@patch("stoa_core.research.web.get_settings")
def test_research_web_tavily(mock_settings):
    settings = MagicMock()
    settings.tavily_api_key = "tvly-test"
    settings.jina_api_key = None
    mock_settings.return_value = settings

    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [
            {
                "url": "https://example.com",
                "title": "Example",
                "content": "Example company info",
                "score": 0.9,
            }
        ]
    }
    mock_tavily = MagicMock()
    mock_tavily.TavilyClient.return_value = mock_client
    with patch.dict("sys.modules", {"tavily": mock_tavily}):
        result = research_web("Acme Corp SaaS")
    assert len(result.items) == 1
    assert result.items[0].title == "Example"


@patch("stoa_core.research.web.get_settings")
def test_research_web_jina_fallback(mock_settings):
    settings = MagicMock()
    settings.tavily_api_key = ""
    settings.jina_api_key = None
    mock_settings.return_value = settings

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": [{"url": "https://b.com", "title": "B", "content": "content"}]
    }
    mock_resp.raise_for_status = MagicMock()
    with patch("stoa_core.research.web.httpx.Client") as client_cls:
        client_cls.return_value.__enter__.return_value.get.return_value = mock_resp
        result = research_web("query")
    assert len(result.items) == 1
    assert "TAVILY" in result.warnings[0]
