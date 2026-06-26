from __future__ import annotations

import logging
from urllib.parse import quote_plus, urlparse

import httpx

from stoa_core.config import get_settings
from stoa_core.research.types import ResearchItem, ResearchResult

logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 25.0


def _clip(text: str | None, limit: int) -> str:
    cleaned = " ".join((text or "").split())
    return cleaned[:limit]


def _prefer_jina_extract(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    blocked = (
        "reddit.com",
        "x.com",
        "twitter.com",
        "linkedin.com",
    )
    return any(host == d or host.endswith(f".{d}") for d in blocked)


def _jina_extract(url: str, api_key: str | None) -> str:
    try:
        headers: dict[str, str] = {"Accept": "text/plain", "x-respond-with": "markdown"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.get(f"https://r.jina.ai/{url}", headers=headers)
            resp.raise_for_status()
            return _clip(resp.text, 3500)
    except Exception as exc:
        logger.debug("Jina extract failed for %s: %s", url, exc)
        return ""


def research_web(query: str, *, max_results: int = 8, product_context: str = "") -> ResearchResult:
    settings = get_settings()
    q = (query or product_context or "").strip()[:400]
    items: list[ResearchItem] = []
    warnings: list[str] = []

    if settings.tavily_api_key:
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=settings.tavily_api_key)
            resp = client.search(
                query=q,
                max_results=max_results,
                search_depth="advanced",
                include_answer=True,
            )
            for row in resp.get("results", [])[:max_results]:
                url = row.get("url") or ""
                use_jina = url and _prefer_jina_extract(url)
                extracted = _jina_extract(url, settings.jina_api_key) if use_jina else ""
                content = row.get("content") or extracted or ""
                items.append(
                    ResearchItem(
                        source_type="web",
                        source_url=url or None,
                        query=q,
                        title=_clip(row.get("title"), 240),
                        raw_excerpt=_clip(content, 2200),
                        summary=_clip(content, 700),
                        confidence=float(row.get("score") or 0.6),
                        metadata={"provider": "tavily+jina" if extracted else "tavily"},
                    )
                )
        except Exception as exc:
            warnings.append(f"Tavily research failed, trying Jina search fallback: {exc}")
    else:
        warnings.append("TAVILY_API_KEY not configured; using Jina search fallback.")

    if not items:
        try:
            headers: dict[str, str] = {"Accept": "application/json"}
            if settings.jina_api_key:
                headers["Authorization"] = f"Bearer {settings.jina_api_key}"
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                resp = client.get(f"https://s.jina.ai/{quote_plus(q)}", headers=headers)
                resp.raise_for_status()
                data = resp.json()
            results = data if isinstance(data, list) else data.get("data", [])
            for row in results[:max_results]:
                content = row.get("content") or ""
                items.append(
                    ResearchItem(
                        source_type="web",
                        source_url=row.get("url"),
                        query=q,
                        title=_clip(row.get("title"), 240),
                        raw_excerpt=_clip(content, 2200),
                        summary=_clip(content, 700),
                        confidence=0.55,
                        metadata={"provider": "jina-search"},
                    )
                )
        except Exception as exc:
            warnings.append(f"Jina search fallback failed: {exc}")

    return ResearchResult(source_type="web", items=_dedupe(items), warnings=warnings)


def _dedupe(items: list[ResearchItem]) -> list[ResearchItem]:
    seen: set[str] = set()
    out: list[ResearchItem] = []
    for item in items:
        key = item.source_url or f"{item.source_type}:{item.title}:{item.raw_excerpt[:80]}"
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out
