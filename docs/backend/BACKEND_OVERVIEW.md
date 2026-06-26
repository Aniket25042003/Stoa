# Backend Overview

**One-liner:** FastAPI thin layer plus Celery workers orchestrating shared `stoa_core` business logic.

## Why it exists

Marketing intelligence workloads split naturally into synchronous API concerns (auth, RBAC, enqueue) and long-running background jobs (ingestion, ICP build, competitive scans). A thin FastAPI layer keeps HTTP handlers small while `stoa_core` holds testable domain logic shared by API and workers.

## How it works

1. **Request entry** — `services/api/app/main.py` creates the FastAPI app, applies security headers + CORS, and registers 15 routers under `/v1`.
2. **Auth & org scope** — `app/deps/auth.py` verifies Supabase JWT; `app/deps/org_scope.py` resolves active org from `X-Org-Id` header → `user_profiles.last_active_org_id` → sole membership.
3. **Permission checks** — `app/services/org_context.py` + `stoa_core.security.permissions` enforce `resource:action` RBAC before writes.
4. **Sync path** — Routers read/write Postgres via `get_supabase_admin()` (service role with membership checks).
5. **Async path** — Routers call `.delay()` on Celery tasks; workers run the same `stoa_core` functions.
6. **Shared package** — `services/core/src/stoa_core/` contains ingestion, RAG, LLM routing, integrations, and security utilities.

## Architecture diagram

```
┌─────────────────────────────────────────────────────────────┐
│  services/api/                                               │
│  ├── app/main.py          FastAPI entry                       │
│  ├── app/routers/         REST + SSE endpoints                │
│  ├── app/tasks/           Celery task definitions             │
│  ├── app/deps/            auth, org_scope, rate_limit         │
│  └── app/services/        audit, invites, task_context        │
└───────────────────────────┬─────────────────────────────────┘
                            │ imports
┌───────────────────────────▼─────────────────────────────────┐
│  services/core/src/stoa_core/                                │
│  ├── config.py            Settings from env                   │
│  ├── db/supabase.py       Admin + anon clients                │
│  ├── ingestion/           chunk, embed, extract               │
│  ├── rag/                 ingest, retrieve, rerank, answer    │
│  ├── llm/router.py        Multi-provider LLM                  │
│  ├── intelligence/        ICP build, CRM stats                │
│  ├── integrations/        14 OAuth/API connectors             │
│  └── redis/               SSE streams, KB cache               │
└───────────────────────────┬─────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
    Supabase Postgres   Redis (Celery + SSE)   LLM providers
```

## Directory structure

| Path | Purpose |
|------|---------|
| `services/api/app/routers/` | HTTP route handlers grouped by feature |
| `services/api/app/tasks/` | Celery task wrappers calling `stoa_core` |
| `services/api/app/deps/` | FastAPI dependencies (auth, rate limit, org scope) |
| `services/api/app/services/` | API-specific helpers (audit, invites, task guard) |
| `services/core/src/stoa_core/` | Shared domain logic (no HTTP) |
| `services/worker/` | Thin `requirements.txt` for separate worker deploy |

## Key code callouts

- **`app/main.py`** — Router registration, production hard-requires for `INVITE_TOKEN_PEPPER` and `INTERNAL_PROXY_SECRET`.
- **`stoa_core/config.py`** — `Settings` class; single source of truth for env vars via pydantic-settings.
- **`app/celery_app.py`** — Celery instance with task allowlist guard via `assert_allowed_task`.
- **`app/services/task_context.py`** — Validates org ownership before workers process jobs.

## Environment variables

| Category | Variables | Purpose |
|----------|-----------|---------|
| Deployment | `STOA_ENV`, `INTERNAL_PROXY_SECRET`, `CORS_ORIGINS`, `APP_BASE_URL`, `API_BASE_URL` | Environment mode, proxy auth, CORS |
| Supabase | `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET`, `STORAGE_BUCKET` | DB, auth, storage |
| Redis/Celery | `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `REDIS_REQUIRE_TLS`, `REDIS_SSL_VERIFY` | Broker, SSE, cache |
| Auth/security | `INVITE_TOKEN_PEPPER`, `INTEGRATION_CREDENTIALS_KEY`, `RATE_LIMIT_PER_MINUTE` | Invites, credential encryption, rate limits |
| LLM | `LLM_PROVIDER`, `LLM_AUTO_FAILOVER`, `VERTEX_*`, `OPENAI_*`, `ANTHROPIC_*`, `STOA_LLM_*` | Provider routing |
| Embeddings/RAG | `EMBED_*`, `RETRIEVAL_*`, `COHERE_*`, `KB_*_TTL_SECONDS`, `CHUNK_*` | Hybrid retrieval pipeline |
| Integrations | `HUBSPOT_*`, `GONG_*`, `SALESFORCE_*`, `ZENDESK_*`, `APIFY_API_TOKEN` | OAuth and data connectors |

Full template: [`services/api/.env.example`](../../services/api/.env.example).

## Tech decisions

1. **Thin API + fat core** — Business logic lives in `stoa_core` so pytest can test without HTTP; API only handles transport.
2. **Service role + membership checks** — API bypasses RLS with service role but validates org membership in application code (avoids anon-client write pitfalls).
3. **Task allowlist** — `task_prerun` signal rejects unknown Celery task names to prevent arbitrary code execution.

## Talking points

- Monorepo split: deploy API + worker from `services/api`; `services/worker` is just a dependency pin.
- Production disables OpenAPI/Swagger (`openapi_url=None`).
- All sensitive writes go through `write_audit()` for compliance trail.
