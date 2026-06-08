# Legacy code archive

This directory contains the previous GTM multi-agent and marketing chat backend, archived during the greenfield rebuild (July 2026).

**Do not deploy from `legacy/`.** It is kept for reference when copying patterns (JWT auth, SSE, LLM router, pgvector KB).

- `legacy/services/api` — old FastAPI + Celery
- `legacy/services/agents` — LangGraph GTM + marketing agents
- `legacy/services/mcp` — MCP research server stub
- `legacy/supabase/migrations` — old schema migrations
