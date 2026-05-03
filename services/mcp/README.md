# MCP research server

`research_server.py` exposes the same production research integrations used by the FastAPI/Celery pipeline as stdio MCP tools.

Run from the repo root after installing `services/api/requirements.txt`:

```bash
PYTHONPATH=services/agents/src python services/mcp/research_server.py
```

Available tools:

- `crawl_web` — deep-read known URLs with Crawlee + Playwright (headless Chromium)
- `crawl_search_results` — Tavily/Jina discovery, then shallow browser crawl of top hits
- `web_research`
- `competitor_research`
- `full_research_suite`

Each discovery-style tool accepts `query`, optional `product_context`, and optional `max_results`.
`crawl_web` accepts `start_urls` plus crawl tuning knobs (`max_pages`, `max_depth`, `same_domain_only`, …).
Each tool returns the normalized source schema documented in `AGENT.md`.

The LangGraph research supervisor lists these tools at runtime and lets the
configured model choose which tools to call. Set `GTM_AGENT_MODEL` and the
provider key (for example `OPENAI_API_KEY`) to enable model-driven tool choice.
