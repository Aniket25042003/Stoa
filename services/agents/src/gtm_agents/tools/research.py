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
from urllib.parse import quote_plus

import httpx
from gtm_agents.state import ResearchItem

SourceType = Literal["reddit", "x", "web", "serp", "other"]
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


def research_reddit(plan: dict[str, Any], max_results: int = 8) -> ResearchToolResult:
    """Search Reddit via PRAW using app credentials."""
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "gtm-agent/0.1")
    if not client_id or not client_secret:
        return _result("reddit", [], ["Reddit research skipped: REDDIT_CLIENT_ID/REDDIT_CLIENT_SECRET are not configured."])

    try:
        import praw  # type: ignore
    except ImportError:
        return _result("reddit", [], ["Reddit research skipped: install praw to enable Reddit collection."])

    query = _source_query(plan, "reddit")
    items: list[ResearchItem] = []
    try:
        reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent, check_for_async=False)
        for submission in reddit.subreddit("all").search(query, sort="relevance", limit=max_results):
            permalink = f"https://www.reddit.com{submission.permalink}"
            body = _clip(getattr(submission, "selftext", "") or getattr(submission, "title", ""), 1800)
            title = _clip(getattr(submission, "title", ""), 240)
            items.append(
                {
                    "source_type": "reddit",
                    "source_url": permalink,
                    "query": query,
                    "title": title,
                    "raw_excerpt": body or title,
                    "summary": _clip(body or title, 500),
                    "sentiment": _sentiment(f"{title} {body}"),
                    "confidence": 0.72,
                    "retrieved_at": _now(),
                    "metadata": {
                        "subreddit": str(getattr(submission, "subreddit", "")),
                        "score": getattr(submission, "score", None),
                        "num_comments": getattr(submission, "num_comments", None),
                    },
                }
            )
    except Exception as e:  # Network/API failures should not kill the whole GTM run.
        return _result("reddit", items, [f"Reddit research partial failure: {e}"])
    return _result("reddit", items)


def research_x(plan: dict[str, Any], max_results: int = 10) -> ResearchToolResult:
    """Search recent public X/Twitter posts via X API v2."""
    bearer = os.getenv("X_API_BEARER_TOKEN")
    if not bearer:
        return _result("x", [], ["X research skipped: X_API_BEARER_TOKEN is not configured."])

    query = f"{_source_query(plan, 'x')} lang:en -is:retweet"
    params = {
        "query": query[:512],
        "max_results": max(10, min(max_results, 100)),
        "tweet.fields": "created_at,public_metrics,author_id,lang",
    }
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.get(
                "https://api.twitter.com/2/tweets/search/recent",
                params=params,
                headers={"Authorization": f"Bearer {bearer}"},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return _result("x", [], [f"X research failed: {e}"])

    items: list[ResearchItem] = []
    for tweet in data.get("data", [])[:max_results]:
        text = _clip(tweet.get("text"), 1800)
        tweet_id = tweet.get("id")
        author_id = tweet.get("author_id")
        items.append(
            {
                "source_type": "x",
                "source_url": f"https://x.com/i/web/status/{tweet_id}" if tweet_id else None,
                "query": query[:512],
                "title": _clip(text, 120),
                "raw_excerpt": text,
                "summary": _clip(text, 500),
                "sentiment": _sentiment(text),
                "confidence": 0.65,
                "retrieved_at": _now(),
                "metadata": {
                    "tweet_id": tweet_id,
                    "author_id": author_id,
                    "created_at": tweet.get("created_at"),
                    "public_metrics": tweet.get("public_metrics", {}),
                },
            }
        )
    return _result("x", items)


def _jina_read_url(url: str) -> str:
    return f"https://r.jina.ai/{url}"


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
                extracted = _jina_extract(url) if url else ""
                content = extracted or r.get("content") or ""
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
                        "metadata": {"provider": "tavily+jina" if extracted else "tavily"},
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


def run_research_suite(plan: dict[str, Any]) -> ResearchToolResult:
    """Run all configured research integrations and return a merged result."""
    if os.getenv("GTM_DISABLE_EXTERNAL_RESEARCH") == "true":
        return _result("other", [], ["External research disabled by GTM_DISABLE_EXTERNAL_RESEARCH=true."])

    merged_items: list[ResearchItem] = []
    warnings: list[str] = []
    for tool in (research_reddit, research_x, research_web, research_competitors):
        try:
            result = tool(plan)
        except Exception as e:
            warnings.append(f"{tool.__name__} crashed: {e}")
            continue
        merged_items.extend(result["items"])
        warnings.extend(result["warnings"])
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
