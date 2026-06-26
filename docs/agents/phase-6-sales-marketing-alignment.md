# Phase 6 — Sales–Marketing Alignment

## Scope

- CRM attribution fields on canonical contacts/deals (`lead_source`, UTM columns)
- Lead conversion, campaign revenue, and deal stall aggregations
- Precomputed alignment insights (`precomputed_insights` scope=`alignment`)
- Alignment workspace at `/alignment`
- API: `/v1/alignment`

## Data flow

1. HubSpot/Salesforce sync → attribution columns + KB ingest
2. Celery `alignment.precompute` → CRM + friction signals + RAG synthesis
3. UI: dual Marketing/Sales panels + shared friction insight

## Exit criteria

- [x] Canonical attribution columns + RLS
- [x] HubSpot/Salesforce attribution field sync
- [x] `stoa_core/alignment/*` + precompute task
- [x] `/v1/alignment` router + `/alignment` workspace
- [x] Permissions: `alignment:read`, `alignment:refresh`
- [x] Chained after CRM integration sync

## Key files

- `supabase/migrations/20260712000000_campaign_analysis_alignment.sql`
- `services/core/src/stoa_core/alignment/`
- `services/core/src/stoa_core/integrations/attribution.py`
- `services/api/app/tasks/alignment.py`
- `services/api/app/routers/alignment.py`
- `apps/web/src/app/(app)/alignment/`

## MVP boundaries

- Contact-level attribution (deal-contact association API deferred)
- No HubSpot marketing email engagement stats yet
- Stall detection via `updated_at` threshold (30 days), not stage history API
