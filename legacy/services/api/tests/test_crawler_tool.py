"""Optional live Crawlee/Playwright check — default CI stays offline."""

from __future__ import annotations

import os

import pytest


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_CRAWLER_TEST", "").strip() != "1",
    reason="Set RUN_LIVE_CRAWLER_TEST=1 to run live browser crawl (requires playwright install chromium).",
)
def test_crawl_web_example_com() -> None:
    from gtm_agents.tools.crawler import crawl_web

    out = crawl_web(
        ["https://example.com"],
        max_pages=1,
        max_depth=0,
        respect_robots=True,
        product_context="smoke",
    )
    assert out["source_type"] == "crawl"
    assert isinstance(out.get("items"), list)
    assert len(out["items"]) >= 1
    first = out["items"][0]
    assert first.get("source_type") == "crawl"
    assert "example.com" in (first.get("source_url") or "")


def test_crawl_disabled_flag() -> None:
    from gtm_agents.tools.crawler import crawl_web

    os.environ["GTM_DISABLE_EXTERNAL_RESEARCH"] = "true"
    try:
        out = crawl_web(["https://example.com"], max_pages=1, max_depth=0)
        assert out["items"] == []
        assert any("GTM_DISABLE_EXTERNAL_RESEARCH" in w for w in out.get("warnings") or [])
    finally:
        os.environ.pop("GTM_DISABLE_EXTERNAL_RESEARCH", None)
