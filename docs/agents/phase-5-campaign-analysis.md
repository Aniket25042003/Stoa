# Phase 5 — Campaign Analysis

## Scope

- Structured analytics metrics from GA4 and PostHog (`analytics_metric_facts`)
- Precomputed campaign performance insights (`precomputed_insights` scope=`campaign_analysis`)
- Campaign analysis workspace at `/campaign-analysis`
- API: `/v1/campaign-analysis`

## Data flow

1. GA4/PostHog sync → dual-write `analytics_metric_facts` + KB (`campaign_metrics`, `product_analytics_summary`)
2. Celery `campaign_analysis.precompute` → aggregations + RAG synthesis → `precomputed_insights`
3. UI reads summary + metrics; ad-hoc Q&A via `/v1/conversations/ask`

## Exit criteria

- [x] Migration + RLS on `analytics_metric_facts`
- [x] GA4/PostHog connector dual-write
- [x] `stoa_core/analytics/*` aggregations + precompute task
- [x] `/v1/campaign-analysis` router + `/campaign-analysis` workspace
- [x] Permissions: `campaign_analysis:read`, `campaign_analysis:refresh`
- [x] Chained after analytics integration sync

## Key files

- `supabase/migrations/20260712000000_campaign_analysis_alignment.sql`
- `services/core/src/stoa_core/analytics/`
- `services/core/src/stoa_core/integrations/ga4.py`
- `services/core/src/stoa_core/integrations/posthog.py`
- `services/api/app/tasks/campaign_analysis.py`
- `services/api/app/routers/campaign_analysis.py`
- `apps/web/src/app/(app)/campaign-analysis/`

## MVP boundaries

- No paid ad platform connectors (Google Ads, LinkedIn Ads)
- Last-touch attribution via UTM + channel groups only
- Batch refresh on sync + manual refresh (no real-time streaming)
