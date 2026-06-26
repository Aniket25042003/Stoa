# Celery Workers

**One-liner:** Background job queue for ingestion, intelligence, competitive, campaigns, and integrations.

## Why it exists

Document processing, embedding, ICP rebuilds, and competitive scans take seconds to minutes. Celery + Redis decouples these from HTTP request timeouts, enables retries, and allows horizontal worker scaling on Render.

## How it works

1. **Celery app** — [`services/api/app/celery_app.py`](../../services/api/app/celery_app.py) configures broker (`REDIS_URL`), JSON serialization, late acks, prefetch=1.
2. **Task allowlist** — `@task_prerun` signal calls `assert_allowed_task()` — rejects unknown task names.
3. **API enqueues** — Routers call `.delay()` or `.apply_async()` after validating org scope.
4. **Worker executes** — Same Python package as API; imports `stoa_core` directly.
5. **Progress events** — Tasks call `publish_event()` → Redis streams → SSE to frontend.
6. **Retries** — `bind=True, max_retries=2-3` with exponential countdown.

## All Celery tasks

| Task name | File | Trigger | What it does | Schedule |
|-----------|------|---------|--------------|----------|
| `ingestion.process_job` | `tasks/ingestion.py` | Upload/paste completes | KB ingest + signal extract + ICP/insights chain | On demand |
| `intelligence.precompute_insights` | `tasks/intelligence.py` | Post-ingest, manual refresh | Precomputes insight Q&A + executive summary | On demand |
| `intelligence.rebuild_icp` | `tasks/intelligence.py` | Post-ingest, post-sync | Builds ICP profile from signals + CRM stats | On demand |
| `intelligence.answer_question` | `tasks/intelligence.py` | `POST /v1/conversations/ask` | Retrieve + LLM answer + persist message | On demand |
| `competitive.monitor` | `tasks/competitive.py` | Manual scan or scheduled | Fetch competitor page, diff, alert, KB ingest | On demand |
| `campaigns.generate` | `tasks/campaigns.py` | `POST /v1/campaigns` | Retrieve context + generate assets | On demand |
| `knowledge.reembed_org` | `tasks/knowledge.py` | Admin/backfill | Re-ingest all org documents + profiles | On demand |
| `integrations.sync_source` | `tasks/integrations.py` | Integration sync button/webhook | Pull CRM/call data → canonical tables + KB | On demand |
| `enrichment.enrich_company` | `tasks/enrichment.py` | Onboarding complete, org profile PATCH | Web research + KB ingest for company | On demand |
| `enrichment.enrich_competitor` | `tasks/enrichment.py` | Competitor add/update/scan | Deep competitor research + KB ingest | On demand |
| `enrichment.checkpoint_conversation` | `tasks/enrichment.py` | After agent answer (every N turns) | Conversation memory checkpoints | On demand |
| `enrichment.schedule_competitor_rescans` | `tasks/enrichment.py` | Celery Beat (daily) | Re-scan all tracked competitors | Scheduled |
| `intelligence.schedule_precompute` | `tasks/enrichment.py` | Celery Beat (weekly) | Refresh stale precomputed insights | Scheduled |
| `integrations.schedule_syncs` | `tasks/enrichment.py` | Celery Beat (daily) | Re-sync active integrations | Scheduled |
| `enrichment.cleanup_stale_jobs` | `tasks/enrichment.py` | Celery Beat (daily) | Fail stuck enrichment jobs | Scheduled |

Celery Beat runs via `services/api/scripts/render_start_beat.sh` (separate Render service).

Previously: no cron/beat — now Beat handles scheduled memory maintenance; user-triggered enrichment remains event-driven.

## Architecture diagram

```
FastAPI router
      │ .delay()
      ▼
Redis broker (Celery)
      │
      ▼
Celery worker (services/api)
      ├── task_context.verify_*()
      ├── stoa_core.* (business logic)
      ├── Supabase (service role)
      └── publish_event() → Redis stream → SSE
```

## Redis broker setup

- **Broker URL**: `CELERY_BROKER_URL` or fallback to `REDIS_URL`
- **Result backend**: Same Redis instance
- **TLS**: Enforced in production via `validate_redis_security()`
- **Queue**: Default `stoa` queue

## Retry logic

| Task | max_retries | countdown |
|------|-------------|-----------|
| `ingestion.process_job` | 3 | 30s |
| `intelligence.*` | 2 | 60s |
| `competitive.monitor` | 2 | 120s |
| `campaigns.generate` | 2 | 60s |
| `knowledge.reembed_org` | 2 | 120s |
| `integrations.sync_source` | 2 | 120s |

## Key code callouts

- **`celery_app.py`** — Worker config: late ack, reject on worker lost, prefetch=1.
- **`task_context.py`** — `ALLOWED_CELERY_TASKS` frozenset; org ownership validation.
- **`publish_event()`** — Redis streams with 10k maxlen, 72h TTL.

## Tech decisions

1. **Celery over cron** — Jobs are triggered by user actions (upload, ask, sync), not time-based; Celery handles retries and backpressure.
2. **Same package as API** — Workers import `app.tasks.*` directly; no separate worker codebase.
3. **Task allowlist** — Security guard against arbitrary task injection.

## Talking points

- Local dev: `services/api/scripts/dev_worker.sh` (solo pool on macOS).
- Production: `render_start.sh` runs Celery + uvicorn in one process (solo pool).
- `services/worker/requirements.txt` is a thin deploy wrapper — no worker-specific code.
