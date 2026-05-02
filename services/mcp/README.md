# MCP research server

`research_server.py` exposes the same production research integrations used by the FastAPI/Celery pipeline as stdio MCP tools.

Run from the repo root after installing `services/api/requirements.txt`:

```bash
PYTHONPATH=services/agents/src python services/mcp/research_server.py
```

Available tools:

- `reddit_research`
- `x_research`
- `web_research`
- `competitor_research`
- `full_research_suite`

Each tool accepts `query`, optional `product_context`, and optional `max_results`.
Each tool returns the normalized source schema documented in `AGENT.md`.

The LangGraph research supervisor lists these tools at runtime and lets the
configured model choose which tools to call. Set `GTM_AGENT_MODEL` and the
provider key (for example `OPENAI_API_KEY`) to enable model-driven tool choice.
