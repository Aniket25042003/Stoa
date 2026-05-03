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
- Optional LangSmith (worker only): `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` — see [LangGraph observability](https://docs.langchain.com/oss/python/langgraph/observability). Legacy `LANGCHAIN_TRACING_V2` / `LANGCHAIN_API_KEY` / `LANGCHAIN_PROJECT` are still mapped when `LANGSMITH_*` is unset.
- Optional research: `TAVILY_API_KEY`, `JINA_API_KEY`, `SERPAPI_API_KEY`, and crawler envs (`GTM_CRAWLER_*`, `CRAWLEE_STORAGE_DIR`) — see `services/api/.env.example`
- **Playwright browsers (API + worker):** after `pip install -r requirements.txt`, run `playwright install chromium --with-deps` locally or rely on `services/api/nixpacks.toml` on Railway so the Celery worker can run `PlaywrightCrawler`.

## Supabase

1. Create project → copy URL, anon key, service role, JWT secret.
2. Run SQL in `supabase/migrations/20250501000000_init_gtm.sql` (SQL editor or CLI).
3. Enable Auth email provider for magic links.
4. Add Site URL + Redirect URLs for Vercel preview/prod.

## Smoke checks

1. `GET https://<api>/health` → `{"status":"ok"}`
2. Sign in on web → create run → events stream → report Markdown returned.

## Observability

- LangSmith: set `LANGSMITH_TRACING=true` on the **Celery worker** only; never expose keys to the browser. Traces include graph nodes, agent planning/approval spans, MCP tool calls, and research provider tools. Each completed pipeline stores `langsmith_correlation` in `agent_artifacts` when trace IDs are available; progress events also include `langsmith_trace_id` / `langsmith_run_id` in `detail` when inside a trace.
- API logs: Railway logs; correlate `run_id` in `run_events` table and filter LangSmith by metadata `run_id` or tag `run:<uuid>`.

## Rollback

- Vercel: promote previous deployment or git revert.
- Railway: redeploy previous image / commit.
- DB: migrations are forward-only; add new migration to revert schema if needed.

