# Phase 2 — Competitive Intelligence

## Scope

- Competitor registry (name, website, pricing URL)
- On-demand and queued website scans
- Change detection + diff summarization
- competitive_alerts table
- Competitive dashboard UI

## Hardening

- User-Agent identification
- Request timeouts
- robots.txt respect (future: parse and skip disallowed paths)
- Outbound rate limits per org

## Exit criteria

- [x] Add competitor → scan queued → snapshot stored
- [x] Changes create alerts
- [x] Frontend competitive page

## Key files

- `supabase/migrations/20260701000003_competitive_schema.sql`
- `services/core/src/stoa_core/competitive/monitor.py`
- `services/api/app/routers/competitive.py`
- `apps/web/src/app/(app)/competitive/`

## Future

- Celery beat for scheduled scans (evaluate vs Temporal per ADR-002)
