from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from gtm_agents.tools.crawler import crawl_search_results as crawl_search_results_fn
from gtm_agents.tools.crawler import crawl_web as crawl_web_fn
from gtm_agents.tools.research import (
    research_plan,
    research_competitors,
    research_web,
    run_research_suite,
)

mcp = FastMCP("gtm-research")


@mcp.tool(name="crawl_web")
def crawl_web(
    start_urls: list[str],
    keywords: str = "",
    max_pages: int = 15,
    max_depth: int = 2,
    same_domain_only: bool = True,
    include_url_patterns: list[str] | None = None,
    exclude_url_patterns: list[str] | None = None,
    respect_robots: bool = True,
    product_context: str = "",
) -> dict[str, Any]:
    """Deep-read specific URLs with a headless browser (Crawlee + Playwright).

    Use when you already have high-value targets: competitor docs, pricing pages, changelogs, forums, blogs,
    help centers, or PDF landing pages that need rendered HTML. Prefer focused `start_urls` (1–5 domains) and
    keep `max_pages` modest to control latency. Set `same_domain_only=false` only when you intentionally need
    cross-site follow-through. Honors robots.txt when `respect_robots=true`.
    """
    return crawl_web_fn(
        start_urls,
        keywords=keywords,
        max_pages=max_pages,
        max_depth=max_depth,
        same_domain_only=same_domain_only,
        include_url_patterns=include_url_patterns,
        exclude_url_patterns=exclude_url_patterns,
        respect_robots=respect_robots,
        product_context=product_context,
    )


@mcp.tool(name="crawl_search_results")
def crawl_search_results(
    query: str,
    max_results: int = 6,
    max_pages_per_result: int = 3,
    max_depth: int = 1,
    product_context: str = "",
) -> dict[str, Any]:
    """Discover URLs via open-web search, then render top hits with Playwright.

    Use when you need both SERP-style discovery and on-page evidence in one call—for example mapping a category,
    pulling competitor positioning lines, or verifying claims on ranked pages. Starts from Tavily/Jina results,
    then crawls shallowly per result. Good default when you do not yet have canonical URLs.
    """
    return crawl_search_results_fn(
        query,
        max_results=max_results,
        max_pages_per_result=max_pages_per_result,
        max_depth=max_depth,
        product_context=product_context,
    )


@mcp.tool()
def web_research(query: str, product_context: str = "", max_results: int = 8) -> dict[str, Any]:
    """Search and extract open-web market research, reports, landing pages, docs, reviews, and buyer guides."""
    return research_web(research_plan("web", query, product_context), max_results=max_results)


@mcp.tool()
def competitor_research(query: str, product_context: str = "", max_results: int = 8) -> dict[str, Any]:
    """Discover competitors, alternatives, comparison pages, pricing pages, and SERP positioning."""
    return research_competitors(research_plan("competitors", query, product_context), max_results=max_results)


@mcp.tool()
def full_research_suite(query: str, product_context: str = "", max_results: int = 8) -> dict[str, Any]:
    """Run every configured research integration when broad coverage is more important than selective tool choice."""
    plan = {
        "product_summary": product_context or query,
        "queries": {
            "web": [query],
            "competitors": [query],
        },
    }
    # max_results is accepted for a consistent MCP surface; individual tools own their caps.
    _ = max_results
    return run_research_suite(plan)


if __name__ == "__main__":
    mcp.run()
