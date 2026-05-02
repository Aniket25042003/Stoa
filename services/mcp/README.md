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

Each tool returns the normalized source schema documented in `AGENT.md`.
