"""Web research utilities for agent memory enrichment."""

from stoa_core.research.distill import (
    distill_company_research,
    distill_competitor_research,
    format_research_bundle,
)
from stoa_core.research.fetch import fetch_page_text, html_to_text
from stoa_core.research.serp import research_competitors
from stoa_core.research.types import ResearchItem, ResearchResult
from stoa_core.research.web import research_web

__all__ = [
    "ResearchItem",
    "ResearchResult",
    "fetch_page_text",
    "html_to_text",
    "research_web",
    "research_competitors",
    "distill_company_research",
    "distill_competitor_research",
    "format_research_bundle",
]
