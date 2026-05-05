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
- **LLM provider (worker + API):** `GTM_LLM_PROVIDER=vertex` (default) or `openai`. Manual switch only — `GTM_LLM_AUTO_FAILOVER=true` (default) automatically falls through to the *other* provider **only when the primary errors**. Vertex needs `GTM_VERTEX_MODEL`, `GTM_VERTEX_PROJECT`, `GTM_VERTEX_LOCATION` and either `GOOGLE_APPLICATION_CREDENTIALS` (service-account JSON path) or workload identity. OpenAI needs `GTM_OPENAI_MODEL` (legacy `GTM_AGENT_MODEL` still honored) and `OPENAI_API_KEY`.
- Optional LangSmith (worker only): `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` — see [LangGraph observability](https://docs.langchain.com/oss/python/langgraph/observability). Legacy `LANGCHAIN_TRACING_V2` / `LANGCHAIN_API_KEY` / `LANGCHAIN_PROJECT` are still mapped when `LANGSMITH_*` is unset.
- Optional research: `TAVILY_API_KEY`, `JINA_API_KEY`, `SERPAPI_API_KEY`, and crawler envs (`GTM_CRAWLER_*`, `CRAWLEE_STORAGE_DIR`) — see `services/api/.env.example`
- **Playwright browsers (API + worker):** after `pip install -r requirements.txt`, run `playwright install chromium --with-deps` locally or rely on `services/api/nixpacks.toml` on Railway so the Celery worker can run `PlaywrightCrawler`.

## Supabase

1. Create project → copy URL, anon key, service role, JWT secret.
2. Apply migrations in `supabase/migrations/` (SQL editor or `supabase db push`).
3. **Auth — Google:** In [Google Cloud Console](https://console.cloud.google.com/auth/clients) create an OAuth **Web application** client. Under **Authorized JavaScript origins** add your app origins (e.g. `http://localhost:3000`, `https://<vercel-domain>`). Under **Authorized redirect URIs** add Supabase’s callback from **Authentication → Providers → Google** (shape: `https://<project-ref>.supabase.co/auth/v1/callback`). Paste the client ID and secret into the Supabase Google provider and enable it. See [Login with Google](https://supabase.com/docs/guides/auth/social-login/auth-google).
4. **Redirect URLs:** In **Authentication → URL Configuration**, set **Site URL** to your primary app URL. Add **Redirect URLs** including `http://localhost:3000/auth/callback` and `https://<vercel-domain>/auth/callback` (and preview URLs if needed).

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

