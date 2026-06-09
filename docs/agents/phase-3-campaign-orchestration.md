# Phase 3 — Campaign Launch Orchestration

## Scope

- Campaign brief intake grounded on ICP + competitive alerts
- Multi-asset generation (messaging, landing, emails, social, battlecard)
- Plain orchestration now; LangGraph for critic/revise loops when needed
- Campaign workspace UI

## Exit criteria

- [x] Create campaign → assets generated async
- [x] Assets stored in campaigns.assets JSONB
- [x] Frontend campaigns page

## Key files

- `supabase/migrations/20260701000004_campaigns_schema.sql`
- `services/core/src/stoa_core/campaign/generate.py`
- `services/api/app/routers/campaigns.py`
- `apps/web/src/app/(app)/campaigns/`

## Future

- LangGraph generate→critic→revise→approve with human gates
- Brand voice profile per org
- Export to PDF/Markdown
