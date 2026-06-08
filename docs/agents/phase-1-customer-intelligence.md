# Phase 1 — Customer / ICP Intelligence

## Scope

- Upload/paste ingestion (CSV, transcripts, reviews, notes)
- Processing: chunk → embed → extract signals → intelligence table
- ICP profile builder (versioned)
- RAG Q&A with citations via conversations/messages
- Intelligence Center UI

## Security

- File type/size/MIME validation
- Content sanitization (prompt-injection patterns)
- PII redaction in stored chunks
- Per-org document quotas
- Rate limiting on ask/upload

## Exit criteria

- [x] Paste content → background job → signals in DB
- [x] ICP rebuild from signals
- [x] Ask question → SSE stream → cited answer
- [x] Frontend Intelligence page

## Key files

- `supabase/migrations/20260701000002_intelligence_schema.sql`
- `services/api/app/routers/ingestion.py`
- `services/api/app/tasks/ingestion.py`
- `services/core/src/stoa_core/ingestion/`
- `apps/web/src/app/(app)/intelligence/`
