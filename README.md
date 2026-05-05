# GTM Multi-Agent Monorepo

See **[AGENT.md](./AGENT.md)** for full architecture and build instructions.

## Quick start

### Prerequisites

- Node 20+, pnpm 9+
- Python 3.11+
- Docker (for local Redis)
- Supabase project (Postgres + Auth)

### Local services

```bash
docker compose up -d redis
```

### Web app

```bash
cp apps/web/.env.example apps/web/.env.local
pnpm install
pnpm dev:web
```

### API + worker

```bash
cd services/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

In another terminal (same venv):

```bash
cd services/api
celery -A app.celery_app worker -l info
```

Set `PYTHONPATH` to include `services/agents` (see `services/api/.env.example`).

### Autonomous research

The LangGraph research supervisor talks to `services/mcp/research_server.py`
over stdio MCP. Configure an LLM provider (Vertex AI by default, OpenAI as
fallback) so the agent can decide which MCP tools to call for each product.
Without any provider, the app uses a conservative broad web-research fallback
instead of fabricating platform-specific findings.

### LLM providers (Vertex primary, OpenAI fallback)

Both providers live behind a single abstraction in
`services/agents/src/gtm_agents/llm.py`. The config is env-driven (see
`services/api/.env.example`):

- `GTM_LLM_PROVIDER` — `vertex` (default) or `openai`. **Manual** switch.
  Change this when you want to move between providers for *quality* reasons.
- `GTM_LLM_AUTO_FAILOVER` — when `true` (default) the app will fall through
  to the other provider **only if the primary raises an error**
  (auth / quota / 5xx / network). Quality-based switching is never automatic.
- Vertex: `GTM_VERTEX_MODEL` (e.g. `gemini-2.5-pro`), `GTM_VERTEX_PROJECT`,
  `GTM_VERTEX_LOCATION`, plus `GOOGLE_APPLICATION_CREDENTIALS` pointing to a
  service-account JSON (or `gcloud auth application-default login` for local).
- OpenAI: `GTM_OPENAI_MODEL` (or legacy `GTM_AGENT_MODEL`) and `OPENAI_API_KEY`.

### LangSmith tracing

On the Celery worker, set `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, and optionally `LANGSMITH_PROJECT` (see [LangGraph observability](https://docs.langchain.com/oss/python/langgraph/observability)). Legacy `LANGCHAIN_TRACING_V2` / `LANGCHAIN_API_KEY` are mapped to LangSmith when the new vars are unset. After a run, check Supabase `agent_artifacts` for `langsmith_correlation` or filter traces by `run_id` metadata.

### User-approved master plan

Creating a run now drafts the main agent's master plan and leaves the run in
`awaiting_plan_approval`. Review or revise the plan in the run detail page, then
approve it to enqueue the Celery pipeline. During execution, main-agent rejection
of research, reasoning, or writing produces revised layer instructions and retries
that layer before failing the run.

## Layout

- `apps/web` — Next.js (Vercel)
- `services/api` — FastAPI + Celery (Railway)
- `services/agents` — LangGraph (`gtm_agents` package)
- `supabase/migrations` — SQL + RLS
