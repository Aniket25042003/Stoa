# Architecture

## Overview

Stoa is a **marketing intelligence platform** built Supabase-first:

- **Frontend:** Next.js 15 App Router, Tailwind v4, Supabase Auth (Google, Azure, email/password)
- **API:** FastAPI thin layer — auth, REST, SSE, job enqueue
- **Worker:** Celery + Redis — ingestion, ICP build, competitive scans, campaigns
- **Core:** `stoa_core` — shared business logic (no HTTP)

## Data flow

```
Auth: Google/Azure/email-password → Supabase Auth → session-state → onboarding/team gates

Any input (docs, profile, ICP, competitive, campaigns, future MCP)
  → ingest_knowledge → knowledge_items + knowledge_chunks (halfvec 3072)

User question / campaign brief / insight prompt
  → retrieve_context (hybrid RRF + rerank + token budget)
  → single LLM synthesis call

Legacy parallel paths (kept for structured queries):
  documents → extract signals → intelligence table → icp_profiles
  Competitor URL → fetch → diff → competitive_alerts
```

Integrations env: `INTEGRATION_CREDENTIALS_KEY`, `HUBSPOT_CLIENT_ID`, `API_BASE_URL`, `APIFY_API_TOKEN`.

## Data flow (integrations)

```
OAuth/API connect → integration_connections (encrypted creds)
  → Celery integrations.sync_source
  → canonical_* tables + ingest_knowledge (KB)
  → extract_signals (interactions) → intelligence
  → rebuild_icp (structured CRM + signals) → precompute_insights
```


## Memory layers

| Layer | Store | Purpose |
|-------|-------|---------|
| Short-term | Redis streams + KB cache | SSE progress, query-embedding cache, retrieval cache |
| Long-term | Postgres | Orgs, documents, intelligence, ICP, campaigns |
| Semantic | pgvector `halfvec(3072)` | Unified `knowledge_chunks` (all features) |
| Structured | Postgres tables | `intelligence` signals, `icp_profiles`, `precomputed_insights` |

## Deployment

- **Web:** Vercel (`apps/web`)
- **API + Worker:** Render (`services/api`, combined via `render_start.sh`)
- **Redis:** Render Key Value
- **DB/Auth/Storage:** Supabase hosted
