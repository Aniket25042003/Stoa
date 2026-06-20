# Ingestion Service

**One-liner:** Upload or paste documents, chunk and embed them into the unified knowledge base.

## Why it exists

Customer intelligence starts with raw data — call transcripts, reviews, CRM exports. Ingestion normalizes this into chunked, embedded, searchable knowledge while extracting structured signals for ICP building.

## How it works

### API entry (sync)

1. `**POST /v1/ingestion/upload`** — `[services/api/app/routers/ingestion.py](../../services/api/app/routers/ingestion.py)` validates file size/type, stores in Supabase Storage, creates `documents` + `ingestion_jobs` rows, enqueues Celery.
2. `**POST /v1/ingestion/paste**` — Same flow for pasted text (no storage path).
3. `**GET /v1/ingestion/jobs/{job_id}**` — Poll job status.

### Celery worker (async)

1. `**ingestion.process_job**` — `[services/api/app/tasks/ingestion.py](../../services/api/app/tasks/ingestion.py)`:
  - Validates job via `verify_ingestion_job()`
  - Sets job status to `running`
  - Calls `ingest_knowledge()` for unified KB write
  - Chunks text again for signal extraction
  - Calls `extract_signals()` per chunk → inserts into `intelligence` table
  - Marks document `processed`, job `completed`
  - Publishes SSE event on Redis stream
  - Chains `rebuild_icp_profile` + `precompute_insights`

### Core pipeline

1. `**ingest_knowledge()**` — `[services/core/src/stoa_core/rag/ingest.py](../../services/core/src/stoa_core/rag/ingest.py)`:
  - Redacts PII via `redact_pii()`
  - Computes `content_hash` for idempotency
  - Skips if unchanged (unless `force=True`)
  - Upserts `knowledge_items` row
  - Chunks via `chunk_text()` with configurable token targets
  - Embeds via `embed_texts()` (Vertex/OpenAI, 3072-dim)
  - Batch-inserts `knowledge_chunks` with embeddings
  - Bumps KB version in Redis (`bump_kb_version`)
2. `**chunk_text()**` — `[services/core/src/stoa_core/ingestion/chunk.py](../../services/core/src/stoa_core/ingestion/chunk.py)` splits on paragraph/sentence boundaries with overlap.
3. `**extract_signals()**` — `[services/core/src/stoa_core/ingestion/extract.py](../../services/core/src/stoa_core/ingestion/extract.py)` uses cheap-tier LLM to classify pain points, objections, buying triggers, etc.

## Architecture diagram

```
User upload/paste
       │
       ▼
FastAPI ingestion router
       │ create documents + ingestion_jobs
       ▼
Celery: ingestion.process_job
       ├── ingest_knowledge ──► knowledge_items + knowledge_chunks (pgvector)
       ├── extract_signals ──► intelligence table
       └── chain: rebuild_icp → precompute_insights
```

## Key code callouts

- `**ingest_knowledge()**` — Idempotent on `uri` + `content_hash`; deletes old chunks on re-ingest.
- `**process_ingestion_job**` — Orchestrates KB write + signal extraction + downstream intelligence tasks.
- `**chunk_text()**` — Default 600 target tokens, 800 max, 80 overlap (env-configurable).
- `**embed_texts()**` — Batch embedding with `EMBED_BATCH_SIZE=32`.

## Data sources ingested


| Source           | Kind                                             | Entry point                                     |
| ---------------- | ------------------------------------------------ | ----------------------------------------------- |
| File upload      | `document`                                       | `/v1/ingestion/upload`                          |
| Paste            | `document`                                       | `/v1/ingestion/paste`                           |
| Integrations     | Various (`crm_account`, `call_transcript`, etc.) | `integrations.sync_source` → `ingest_knowledge` |
| ICP rebuild      | `icp_profile`                                    | `intelligence.rebuild_icp`                      |
| Competitive scan | `competitive_snapshot`                           | `competitive.monitor`                           |
| Campaign output  | `campaign_asset`                                 | `campaigns.generate`                            |


## Metadata attached to chunks

Each chunk carries: `org_id`, `item_id`, `chunk_index`, `kind`, `token_count`, `content_hash`, `embedding`, plus parent item `metadata` jsonb (e.g. `document_id`, `doc_type`).

## Tech decisions

1. **Dual write path** — KB chunks for RAG retrieval + `intelligence` rows for structured ICP queries.
2. **Idempotent ingestion** — Content hash prevents re-embedding unchanged documents, saving cost.
3. **PII redaction at ingest** — Applied before storage and embedding.

## Talking points

- Ingestion triggers a cascade: ICP rebuild → insight precompute (precompute-over-regenerate doctrine).
- Integration syncs use the same `ingest_knowledge()` path — one unified KB for all features.
- Max upload: 10 MB default (`MAX_UPLOAD_BYTES`); 500 documents per org cap.

