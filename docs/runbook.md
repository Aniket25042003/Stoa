# GTM Agent — Production Runbook

## Services


| Service         | Platform                    | Notes                                                                          |
| --------------- | --------------------------- | ------------------------------------------------------------------------------ |
| Web             | Vercel                      | Root directory `apps/web`; set env vars from `apps/web/.env.example`           |
| API             | Railway                     | Root `services/api`; start `uvicorn app.main:app`                              |
| Worker          | Railway                     | Same repo, **second service**; start `celery -A app.celery_app worker -l info` |
| Redis           | Railway (or Docker locally) | `REDIS_URL`, `CELERY_`*                                                        |
| Database + Auth | Supabase                    | Apply migrations in `supabase/migrations/`                                     |


## Required environment

### Vercel (`apps/web`)

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_URL` — public Railway (or staging) API URL

### Railway API + Worker (`services/api`)

- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
- `REDIS_URL` (same for broker if desired)
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- `CORS_ORIGINS` — include `https://<your-vercel-domain>`
- Optional: `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`
- Optional research: `TAVILY_API_KEY`, `SERPAPI_API_KEY`, Reddit/X keys

## Supabase

1. Create project → copy URL, anon key, service role, JWT secret.
2. Run SQL in `supabase/migrations/20250501000000_init_gtm.sql` (SQL editor or CLI).
3. Enable Auth email provider for magic links.
4. Add Site URL + Redirect URLs for Vercel preview/prod.

## Smoke checks

1. `GET https://<api>/health` → `{"status":"ok"}`
2. Sign in on web → create run → events stream → report Markdown returned.

## Observability

- LangSmith: enable on worker only; never expose keys to browser.
- API logs: Railway logs; correlate `run_id` in `run_events` table.

## Rollback

- Vercel: promote previous deployment or git revert.
- Railway: redeploy previous image / commit.
- DB: migrations are forward-only; add new migration to revert schema if needed.

