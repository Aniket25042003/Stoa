"""Crawlee + Playwright web crawling for deep page reads (replaces Reddit/X-specific flows)."""

from __future__ import annotations

import asyncio
import os
import re
import uuid
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from crawlee import ConcurrencySettings, Glob
from crawlee.configuration import Configuration
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

from gtm_agents.observability import traced_tool
from gtm_agents.state import ResearchItem
from gtm_agents.tools.research import (
    ResearchToolResult,
    _clip,
    _now,
    _result,
    _sentiment,
    research_plan,
    research_web,
)


def _env_int(name: str, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _storage_subdir() -> Path:
    base = Path(os.getenv("CRAWLEE_STORAGE_DIR") or "/tmp/crawlee")
    sub = base / f"run-{uuid.uuid4().hex}"
    sub.mkdir(parents=True, exist_ok=True)
    return sub


def _to_globs(patterns: list[str] | None) -> list[Glob] | None:
    if not patterns:
        return None
    return [Glob(p) for p in patterns if p.strip()]


def _keyword_hits(text: str, keywords_csv: str) -> dict[str, int]:
    if not keywords_csv.strip():
        return {}
    hits: dict[str, int] = {}
    lower = text.lower()
    for kw in re.split(r"[,;\n]+", keywords_csv):
        k = kw.strip().lower()
        if len(k) < 2:
            continue
        hits[kw.strip()] = lower.count(k)
    return {k: v for k, v in hits.items() if v > 0}


@dataclass
class CrawlSettings:
    """Parameters for a single crawl (MCP / suite callers map into this)."""

    start_urls: list[str]
    keywords: str = ""
    max_pages: int = 15
    max_depth: int = 2
    same_domain_only: bool = True
    include_url_patterns: list[str] | None = None
    exclude_url_patterns: list[str] | None = None
    request_handler_timeout_secs: int = 45
    min_concurrency: int = 1
    max_concurrency: int = 4
    respect_robots: bool = True
    product_context: str = ""
    query: str = ""


def settings_respect_robots() -> bool:
    return _env_bool("GTM_CRAWLER_RESPECT_ROBOTS", True)


def crawl_settings_from_env_overrides(base: CrawlSettings) -> CrawlSettings:
    """Apply global env caps to a settings object (mutates max_pages/max_depth/concurrency)."""
    max_pages = min(base.max_pages, _env_int("GTM_CRAWLER_MAX_PAGES", 25))
    max_depth = min(base.max_depth, _env_int("GTM_CRAWLER_MAX_DEPTH", 2))
    return CrawlSettings(
        start_urls=base.start_urls,
        keywords=base.keywords,
        max_pages=max(1, max_pages),
        max_depth=max(0, max_depth),
        same_domain_only=base.same_domain_only,
        include_url_patterns=base.include_url_patterns,
        exclude_url_patterns=base.exclude_url_patterns,
        request_handler_timeout_secs=_env_int("GTM_CRAWLER_REQUEST_TIMEOUT_SECS", base.request_handler_timeout_secs),
        min_concurrency=_env_int("GTM_CRAWLER_MIN_CONCURRENCY", base.min_concurrency),
        max_concurrency=_env_int("GTM_CRAWLER_MAX_CONCURRENCY", base.max_concurrency),
        respect_robots=base.respect_robots,
        product_context=base.product_context,
        query=base.query,
    )


def _disabled() -> bool:
    return (os.getenv("GTM_DISABLE_EXTERNAL_RESEARCH") or "").strip().lower() in ("1", "true", "yes")


async def run_crawl(settings: CrawlSettings) -> ResearchToolResult:
    """Run PlaywrightCrawler and return normalized research items."""
    if _disabled():
        return _result("crawl", [], ["External research disabled by GTM_DISABLE_EXTERNAL_RESEARCH=true."])

    settings = crawl_settings_from_env_overrides(settings)

    urls = [u.strip() for u in settings.start_urls if u and u.strip().startswith(("http://", "https://"))]
    if not urls:
        return _result("crawl", [], ["Crawl skipped: no valid http(s) start_urls."])

    items: list[ResearchItem] = []
    warnings: list[str] = []

    storage_dir = _storage_subdir()
    user_agent = (os.getenv("GTM_CRAWLER_USER_AGENT") or "").strip() or "gtm-agent-crawler/0.1 (+https://example.com)"

    enqueue_strategy: Literal["same-hostname", "all"] = "same-hostname" if settings.same_domain_only else "all"
    include = _to_globs(settings.include_url_patterns)
    exclude = _to_globs(settings.exclude_url_patterns)

    configuration = Configuration(storage_dir=str(storage_dir))

    crawler = PlaywrightCrawler(
        configuration=configuration,
        headless=True,
        browser_type="chromium",
        browser_new_context_options={
            "viewport": {"width": 1280, "height": 720},
            "user_agent": user_agent,
        },
        max_request_retries=3,
        max_requests_per_crawl=settings.max_pages,
        max_crawl_depth=settings.max_depth,
        use_session_pool=True,
        retry_on_blocked=True,
        respect_robots_txt_file=settings.respect_robots,
        request_handler_timeout=timedelta(seconds=settings.request_handler_timeout_secs),
        concurrency_settings=ConcurrencySettings(
            min_concurrency=settings.min_concurrency,
            max_concurrency=settings.max_concurrency,
        ),
        configure_logging=False,
    )

    async def _pre_nav_hook(ctx: Any) -> None:
        try:
            await ctx.block_requests()  # images, fonts, stylesheets, media (defaults)
        except Exception:
            pass

    crawler.pre_navigation_hook(_pre_nav_hook)

    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        page = context.page
        depth = int(getattr(context.request, "crawl_depth", 0) or 0)
        title = _clip(await page.title(), 240)
        loaded = getattr(context.request, "loaded_url", None)
        final_url = str(loaded or page.url or context.request.url)
        meta_desc = ""
        try:
            loc = page.locator('meta[name="description"]').first
            if await loc.count() > 0:
                meta_desc = _clip(await loc.get_attribute("content") or "", 400)
        except Exception:
            pass
        body_text = ""
        try:
            body_text = await page.evaluate("() => document.body ? document.body.innerText : ''")
        except Exception:
            body_text = ""
        body_text = _clip(body_text, 3500)
        text_for_kw = f"{title} {meta_desc} {body_text}"
        kw_hits = _keyword_hits(text_for_kw, settings.keywords)
        status: int | None = None
        try:
            if context.response:
                status = context.response.status
        except Exception:
            status = None

        excerpt = _clip(f"{meta_desc + ' — ' if meta_desc else ''}{body_text}", 2200)
        q = settings.query or settings.product_context or settings.keywords or final_url
        items.append(
            {
                "source_type": "crawl",
                "source_url": final_url,
                "query": _clip(q, 512),
                "title": title or final_url,
                "raw_excerpt": excerpt,
                "summary": _clip(excerpt, 700),
                "sentiment": _sentiment(text_for_kw),
                "confidence": 0.62,
                "retrieved_at": _now(),
                "metadata": {
                    "crawl_depth": depth,
                    "final_url": final_url,
                    "requested_url": context.request.url,
                    "status": status,
                    "keyword_hits": kw_hits,
                    "extractor": "crawlee+playwright",
                },
            }
        )

        try:
            await context.enqueue_links(
                strategy=enqueue_strategy,
                include=include,
                exclude=exclude,
            )
        except Exception as e:
            warnings.append(f"enqueue_links failed for {final_url}: {e}")

    async def on_failed(context: PlaywrightCrawlingContext, error: Exception) -> None:
        warnings.append(f"Crawl failed for {context.request.url}: {error}")

    crawler.failed_request_handler(on_failed)

    await crawler.run(urls)
    return _result("crawl", items, warnings)


async def run_search_then_crawl(
    query: str,
    *,
    product_context: str = "",
    max_results: int = 6,
    max_pages_per_result: int = 3,
    max_depth: int = 1,
    same_domain_only: bool = True,
    respect_robots: bool | None = None,
) -> ResearchToolResult:
    """Use Tavily/Jina web search to seed URLs, then deepen with Playwright."""
    if _disabled():
        return _result("crawl", [], ["External research disabled by GTM_DISABLE_EXTERNAL_RESEARCH=true."])

    plan = research_plan("web", query, product_context)
    web = research_web(plan, max_results=max_results)
    seed_urls: list[str] = []
    for it in web.get("items") or []:
        u = (it.get("source_url") or "").strip()
        if u.startswith("http"):
            seed_urls.append(u)
    seed_urls = seed_urls[:max_results]
    wcombine = list(web.get("warnings") or [])

    if not seed_urls:
        return _result("crawl", [], wcombine + ["crawl_search_results: no URLs returned from web search to crawl."])

    respect = settings_respect_robots() if respect_robots is None else respect_robots
    settings = CrawlSettings(
        start_urls=seed_urls,
        keywords=query,
        max_pages=max(1, min(max_pages_per_result * len(seed_urls), _env_int("GTM_CRAWLER_MAX_PAGES", 25))),
        max_depth=max_depth,
        same_domain_only=same_domain_only,
        respect_robots=respect,
        product_context=product_context,
        query=query,
        request_handler_timeout_secs=_env_int("GTM_CRAWLER_REQUEST_TIMEOUT_SECS", 45),
        min_concurrency=_env_int("GTM_CRAWLER_MIN_CONCURRENCY", 1),
        max_concurrency=_env_int("GTM_CRAWLER_MAX_CONCURRENCY", 4),
    )
    crawled = await run_crawl(settings)
    return _result(
        "crawl",
        crawled["items"],
        wcombine + crawled["warnings"],
    )


@traced_tool(name="crawl_web", run_type="tool")
def crawl_web(
    start_urls: list[str],
    keywords: str = "",
    max_pages: int = 15,
    max_depth: int = 2,
    same_domain_only: bool = True,
    include_url_patterns: list[str] | None = None,
    exclude_url_patterns: list[str] | None = None,
    respect_robots: bool | None = None,
    product_context: str = "",
) -> ResearchToolResult:
    """Synchronous entrypoint for MCP: crawl known URLs with Playwright."""
    respect = settings_respect_robots() if respect_robots is None else respect_robots
    settings = crawl_settings_from_env_overrides(
        CrawlSettings(
            start_urls=list(start_urls),
            keywords=keywords,
            max_pages=max_pages,
            max_depth=max_depth,
            same_domain_only=same_domain_only,
            include_url_patterns=include_url_patterns,
            exclude_url_patterns=exclude_url_patterns,
            respect_robots=respect,
            product_context=product_context,
            query=keywords or product_context,
        )
    )
    return asyncio.run(run_crawl(settings))


@traced_tool(name="crawl_search_results", run_type="tool")
def crawl_search_results(
    query: str,
    max_results: int = 6,
    max_pages_per_result: int = 3,
    max_depth: int = 1,
    product_context: str = "",
) -> ResearchToolResult:
    """Search-first crawl: discover URLs via web research, then render pages."""
    return asyncio.run(
        run_search_then_crawl(
            query,
            product_context=product_context,
            max_results=max_results,
            max_pages_per_result=max_pages_per_result,
            max_depth=max_depth,
        )
    )


@traced_tool(name="research_crawl", run_type="tool")
def research_crawl_from_urls(seed_urls: list[str], product_context: str = "") -> ResearchToolResult:
    """Used by run_research_suite to deepen pages already discovered by web/competitor research."""
    if _disabled():
        return _result("crawl", [], ["External research disabled by GTM_DISABLE_EXTERNAL_RESEARCH=true."])
    urls = [u for u in seed_urls if isinstance(u, str) and u.startswith("http")]
    settings = crawl_settings_from_env_overrides(
        CrawlSettings(
            start_urls=urls,
            keywords="",
            max_pages=min(12, max(3, len(urls) * 2)),
            max_depth=1,
            same_domain_only=True,
            respect_robots=settings_respect_robots(),
            product_context=product_context,
            query=product_context,
        )
    )
    return asyncio.run(run_crawl(settings))


def top_http_urls_from_items(items: list[ResearchItem], *, limit: int = 8) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for it in items:
        u = (it.get("source_url") or "").strip()
        if not u.startswith("http"):
            continue
        host = urlparse(u).hostname or ""
        if host.endswith("google.com") and "/search" in u:
            continue
        if u not in seen:
            seen.add(u)
            out.append(u)
        if len(out) >= limit:
            break
    return out
