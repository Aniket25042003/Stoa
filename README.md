# Stoa — Marketing Intelligence Platform

See **[AGENTS.md](./AGENTS.md)** for full architecture and build instructions.

## Quick start

### Prerequisites

- Node 20+, pnpm 9+
- Python 3.11+
- Docker (Redis)
- Supabase project (Postgres + Auth + Storage)

### Local services

```bash
docker compose up -d redis
```

### Apply migrations

```bash
supabase db push
# Or apply SQL in supabase/migrations/ via Supabase dashboard
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

In another terminal:

```bash
cd services/api
source .venv/bin/activate
celery -A app.celery_app worker -l info
```

## Layout

- `apps/web` — Next.js (Vercel)
- `services/api` — FastAPI + Celery tasks
- `services/core` — `stoa_core` shared library
- `legacy/` — archived GTM/marketing code (reference only)
- `supabase/migrations` — greenfield schema

## Product areas

1. **Intelligence** — ICP & customer research (upload/paste → signals → ask)
2. **Competitive** — competitor monitoring & alerts
3. **Campaigns** — brief → multi-asset package
