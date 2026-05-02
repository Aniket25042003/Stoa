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
over stdio MCP. Configure `GTM_AGENT_MODEL` plus a provider key such as
`OPENAI_API_KEY` to let the agent decide which MCP tools to call for each
product. Without a model, the app uses a conservative broad web-research fallback
instead of fabricating platform-specific findings.

## Layout

- `apps/web` — Next.js (Vercel)
- `services/api` — FastAPI + Celery (Railway)
- `services/agents` — LangGraph (`gtm_agents` package)
- `supabase/migrations` — SQL + RLS
