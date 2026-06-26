from __future__ import annotations

import logging

import httpx

from stoa_core.config import get_settings
from stoa_core.research.types import ResearchItem, ResearchResult

logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 25.0


def _clip(text: str | None, limit: int) -> str:
    cleaned = " ".join((text or "").split())
    return cleaned[:limit]


def research_competitors(query: str, *, max_results: int = 8) -> ResearchResult:
    settings = get_settings()
    if not settings.serpapi_api_key:
        return ResearchResult(
            source_type="serp",
            warnings=["SERPAPI_API_KEY not configured; competitor SERP skipped."],
        )

    q = query.strip()[:512]
    params = {
        "engine": "google",
        "q": q,
        "api_key": settings.serpapi_api_key,
        "num": max_results,
    }
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.get("https://serpapi.com/search.json", params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        return ResearchResult(source_type="serp", warnings=[f"Competitor search failed: {exc}"])

    items: list[ResearchItem] = []
    for row in data.get("organic_results", [])[:max_results]:
        snippet = row.get("snippet") or ""
        items.append(
            ResearchItem(
                source_type="serp",
                source_url=row.get("link"),
                query=q,
                title=_clip(row.get("title"), 240),
                raw_excerpt=_clip(str(snippet), 1600),
                summary=_clip(str(snippet), 500),
                confidence=0.68,
                metadata={
                    "position": row.get("position"),
                    "displayed_link": row.get("displayed_link"),
                    "provider": "serpapi",
                },
            )
        )
    return ResearchResult(source_type="serp", items=items)
