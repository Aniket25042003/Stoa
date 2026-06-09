# Phase 1b — Data Hub + Proactive Insights

## Scope

- Central `/data` hub for all shared workspace inputs
- Feature tabs consumption-only with missing-data prompts
- Dashboard live stats + executive summary
- Precomputed intelligence answers (fixed question set)

## Data hub collects

- Company profile (extended JSONB on `organizations.profile`)
- Customer documents (paste/upload)
- Competitors (name + URL)
- Brand voice

## Precompute

- Task: `intelligence.precompute_insights`
- Triggered after ingestion completion and ICP rebuild
- Cost guardrail: skips if document count unchanged (unless `force=True`)
- Stores rows in `precomputed_insights`

## API

- `GET /v1/orgs/me` — includes `completeness`
- `PATCH /v1/orgs/me` — profile fields
- `GET /v1/dashboard/summary` — stats + executive summary
- `GET /v1/intelligence/insights` — prepared answers
- `POST /v1/intelligence/insights/refresh` — manual refresh (rate-limited)

## Exit criteria

- [x] Data hub tab with profile, documents, competitors
- [x] Intelligence/Competitive consumption-only
- [x] Dashboard stat tiles + completeness
- [x] Precomputed common questions
- [x] Tests for completeness + dashboard shape
