from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from gtm_agents.tools.research import (
    research_plan,
    research_competitors,
    research_reddit,
    research_web,
    research_x,
    run_research_suite,
)

mcp = FastMCP("gtm-research")


@mcp.tool()
def reddit_research(query: str, product_context: str = "", max_results: int = 8) -> dict[str, Any]:
    """Search Reddit for voice-of-customer evidence, complaints, alternatives, and community language."""
    return research_reddit(research_plan("reddit", query, product_context), max_results=max_results)


@mcp.tool()
def x_research(query: str, product_context: str = "", max_results: int = 10) -> dict[str, Any]:
    """Search recent public X/Twitter posts for sentiment, trends, launch signals, and category language."""
    return research_x(research_plan("x", query, product_context), max_results=max_results)


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
            "reddit": [query],
            "x": [query],
            "web": [query],
            "competitors": [query],
        },
    }
    # max_results is accepted for a consistent MCP surface; individual tools own their caps.
    _ = max_results
    return run_research_suite(plan)


if __name__ == "__main__":
    mcp.run()
