"""Credential-backed research integrations for the GTM agent.

The functions in this module never fabricate findings. If an integration is not
configured, the caller receives a warning and an empty item list for that source.
Jina search/extract is used as a no-key web fallback because it is a real external
reader API and gives local development an end-to-end research path.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Iterable, Literal, TypedDict
from urllib.parse import quote_plus, urlparse

import httpx
from gtm_agents.observability import traced_tool
from gtm_agents.state import ResearchItem

SourceType = Literal["web", "serp", "crawl", "other"]
DEFAULT_TIMEOUT = 25.0


class ResearchToolResult(TypedDict):
    source_type: SourceType
    items: list[ResearchItem]
    warnings: list[str]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clip(text: str | None, limit: int) -> str:
    cleaned = " ".join((text or "").split())
    return cleaned[:limit]


def _sentiment(text: str) -> str:
    lower = text.lower()
    positive = sum(lower.count(w) for w in ("love", "great", "best", "easy", "fast", "helpful", "recommend"))
    negative = sum(lower.count(w) for w in ("hate", "hard", "expensive", "slow", "broken", "confusing", "problem"))
    if positive > negative:
        return "positive"
    if negative > positive:
        return "negative"
    return "neutral"


def _dedupe(items: Iterable[ResearchItem]) -> list[ResearchItem]:
    seen: set[str] = set()
    out: list[ResearchItem] = []
    for item in items:
        key = item.get("source_url") or f"{item.get('source_type')}:{item.get('title')}:{item.get('raw_excerpt')}"
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _result(source_type: SourceType, items: list[ResearchItem], warnings: list[str] | None = None) -> ResearchToolResult:
    return {"source_type": source_type, "items": _dedupe(items), "warnings": warnings or []}


def _source_query(plan: dict[str, Any], source: str) -> str:
    if plan.get("query"):
        return str(plan["query"])
    queries = (plan.get("queries") or {}).get(source) or []
    if queries:
        return str(queries[0])
    return str(plan.get("product_summary") or "")


def research_plan(source: str, query: str, product_context: str = "") -> dict[str, Any]:
    """Build the compact plan object understood by the underlying integrations."""
    return {
        "product_summary": product_context or query,
        "query": query,
        "queries": {source: [query]},
    }


def _jina_read_url(url: str) -> str:
    return f"https://r.jina.ai/{url}"


def _prefer_jina_extract(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return False
    blocked_hosts = (
        "reddit.com",
        "www.reddit.com",
        "old.reddit.com",
        "x.com",
        "www.x.com",
        "twitter.com",
        "www.twitter.com",
        "linkedin.com",
        "www.linkedin.com",
    )
    return any(host == domain or host.endswith(f".{domain}") for domain in blocked_hosts)


def _jina_extract(url: str) -> str:
    try:
        headers: dict[str, str] = {"Accept": "text/plain", "x-respond-with": "markdown"}
        if os.getenv("JINA_API_KEY"):
            headers["Authorization"] = f"Bearer {os.getenv('JINA_API_KEY')}"
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.get(_jina_read_url(url), headers=headers)
            resp.raise_for_status()
            return _clip(resp.text, 3500)
    except Exception:
        return ""


@traced_tool(name="research_web", run_type="tool")
def research_web(plan: dict[str, Any], max_results: int = 8) -> ResearchToolResult:
    """Search the open web using Tavily when configured, with Jina as extractor/fallback."""
    query = _source_query(plan, "web")
    items: list[ResearchItem] = []
    warnings: list[str] = []

    if os.getenv("TAVILY_API_KEY"):
        try:
            from tavily import TavilyClient  # type: ignore

            client = TavilyClient()
            resp = client.search(
                query=query[:400],
                max_results=max_results,
                search_depth="advanced",
                include_answer=True,
            )
            for r in resp.get("results", [])[:max_results]:
                url = r.get("url") or ""
                # Prefer Tavily snippets by default; reserve Jina extraction for sites that
                # commonly block direct crawling or are awkward to render locally.
                extracted = _jina_extract(url) if url and _prefer_jina_extract(url) else ""
                content = r.get("content") or extracted or ""
                items.append(
                    {
                        "source_type": "web",
                        "source_url": url,
                        "query": query[:400],
                        "title": _clip(r.get("title"), 240),
                        "raw_excerpt": _clip(content, 2200),
                        "summary": _clip(content, 700),
                        "sentiment": None,
                        "confidence": float(r.get("score") or 0.6),
                        "retrieved_at": _now(),
                        "metadata": {
                            "provider": "tavily+jina" if extracted else "tavily",
                            "used_jina_extract": bool(extracted),
                        },
                    }
                )
        except Exception as e:
            warnings.append(f"Tavily research failed, trying Jina search fallback: {e}")
    else:
        warnings.append("Tavily search skipped: TAVILY_API_KEY is not configured; using Jina search fallback.")

    if not items:
        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                resp = client.get(
                    f"https://s.jina.ai/{quote_plus(query[:400])}",
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()
            results = data if isinstance(data, list) else data.get("data", [])
            for r in results[:max_results]:
                content = r.get("content") or ""
                items.append(
                    {
                        "source_type": "web",
                        "source_url": r.get("url"),
                        "query": query[:400],
                        "title": _clip(r.get("title"), 240),
                        "raw_excerpt": _clip(content, 2200),
                        "summary": _clip(content, 700),
                        "sentiment": None,
                        "confidence": 0.55,
                        "retrieved_at": _now(),
                        "metadata": {"provider": "jina-search"},
                    }
                )
        except Exception as e:
            warnings.append(f"Jina search fallback failed: {e}")
    return _result("web", items, warnings)


@traced_tool(name="research_competitors", run_type="tool")
def research_competitors(plan: dict[str, Any], max_results: int = 8) -> ResearchToolResult:
    """Discover competitors and comparison pages using SerpAPI."""
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return _result("serp", [], ["Competitor research skipped: SERPAPI_API_KEY is not configured."])

    query = _source_query(plan, "competitors")
    params = {"engine": "google", "q": query[:512], "api_key": api_key, "num": max_results}
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.get("https://serpapi.com/search.json", params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return _result("serp", [], [f"Competitor search failed: {e}"])

    items: list[ResearchItem] = []
    for r in data.get("organic_results", [])[:max_results]:
        snippet = r.get("snippet") or r.get("rich_snippet", {}).get("top", {}).get("detected_extensions", "")
        items.append(
            {
                "source_type": "serp",
                "source_url": r.get("link"),
                "query": query[:512],
                "title": _clip(r.get("title"), 240),
                "raw_excerpt": _clip(str(snippet), 1600),
                "summary": _clip(str(snippet), 500),
                "sentiment": None,
                "confidence": 0.68,
                "retrieved_at": _now(),
                "metadata": {
                    "position": r.get("position"),
                    "displayed_link": r.get("displayed_link"),
                    "provider": "serpapi",
                },
            }
        )
    return _result("serp", items)


@traced_tool(name="run_research_suite", run_type="tool")
def run_research_suite(plan: dict[str, Any]) -> ResearchToolResult:
    """Run all configured research integrations and return a merged result."""
    if os.getenv("GTM_DISABLE_EXTERNAL_RESEARCH") == "true":
        return _result("other", [], ["External research disabled by GTM_DISABLE_EXTERNAL_RESEARCH=true."])

    merged_items: list[ResearchItem] = []
    warnings: list[str] = []
    for tool in (research_web, research_competitors):
        try:
            result = tool(plan)
        except Exception as e:
            warnings.append(f"{tool.__name__} crashed: {e}")
            continue
        merged_items.extend(result["items"])
        warnings.extend(result["warnings"])

    from gtm_agents.tools.crawler import research_crawl_from_urls, top_http_urls_from_items

    try:
        seed_urls = top_http_urls_from_items(merged_items, limit=8)
        product_context = str(plan.get("product_summary") or _source_query(plan, "web") or "")
        if seed_urls:
            crawl_res = research_crawl_from_urls(seed_urls, product_context=product_context)
            merged_items.extend(crawl_res["items"])
            warnings.extend(crawl_res["warnings"])
        else:
            warnings.append("Suite crawl skipped: no HTTP URLs from web/competitor research to deepen.")
    except Exception as e:
        warnings.append(f"research_crawl_from_urls crashed: {e}")

    return _result("other", merged_items, warnings)


def merge_research(items: list[ResearchItem]) -> dict[str, Any]:
    by_type: dict[str, list[ResearchItem]] = {}
    for it in items:
        t = it.get("source_type") or "other"
        by_type.setdefault(t, []).append(it)
    themes: dict[str, int] = {}
    for it in items:
        text = f"{it.get('title', '')} {it.get('summary', '')}".lower()
        for token in ("price", "pricing", "integrations", "security", "workflow", "automation", "onboarding", "roi", "sales", "content"):
            if token in text:
                themes[token] = themes.get(token, 0) + 1
    return {"by_type": by_type, "count": len(items), "theme_counts": themes}
