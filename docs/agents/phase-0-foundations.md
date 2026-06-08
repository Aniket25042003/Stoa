# Phase 0 — Foundations

## Scope

- Archive legacy `services/` and migrations to `legacy/`
- Greenfield `services/api`, `services/core`, `services/worker`
- Restore Google sign-in
- Baseline tenancy schema (orgs, memberships, audit_log)
- Core platform: config, LLM router, Redis SSE, Celery skeleton
- CI: ruff, pytest, pnpm lint

## Exit criteria

- [x] Google OAuth sign-in works
- [x] `/health` returns ok
- [x] JWT verification (JWKS + HS256)
- [x] Org auto-provision on signup
- [x] AGENTS.md + architecture/security/reliability docs
- [x] CI workflow updated

## Key files

- `supabase/migrations/20260701000001_baseline_tenancy.sql`
- `services/core/src/stoa_core/`
- `services/api/app/main.py`
- `apps/web/src/app/login/page.tsx`
