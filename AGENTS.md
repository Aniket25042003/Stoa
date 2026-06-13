# Stoa Marketing Intelligence — Agent Instructions

**Single source of truth** for coding agents building the Marketing Intelligence platform. Follow phases in order; each sub-phase has a Definition of Done gate.

## Product goal

Marketing teams connect customer data (uploads first; integrations later). The platform **precomputes intelligence** (ICP signals, competitive changes, campaign assets) and answers questions by **retrieving stored evidence + one synthesis call** — not fresh multi-agent research per request.

## Non-negotiable architecture

| Layer | Responsibility |
|-------|----------------|
| **Next.js (Vercel)** | UI, Supabase Auth (Google OAuth), SSE to FastAPI |
| **FastAPI** | REST + SSE, JWT verification, enqueue Celery |
| **Celery + Redis** | Ingestion, ICP build, competitive scans, campaign generation |
| **Supabase** | Postgres + pgvector + Auth + Storage + RLS |
| **stoa_core** | Shared: config, LLM router, ingestion, RAG, security |

**Secrets:** Never expose `SUPABASE_SERVICE_ROLE_KEY` or LLM keys to the browser.

## Doctrine

1. **Precompute, don't regenerate** — background pipelines store intelligence; query path retrieves + synthesizes once.
2. **Explicit memory** — Postgres (long-term), Redis (session/SSE), pgvector (semantic).
3. **Model routing** — cheap models for extract/classify; premium for ICP/campaign synthesis.
4. **Security & reliability every sub-phase** — RLS, audit log, idempotent jobs, tests, docs.

## Monorepo layout

```
├── AGENTS.md              # This file (master agent context)
├── docs/
│   ├── architecture.md
│   ├── security.md
│   ├── reliability.md
│   ├── decisions/         # ADRs
│   └── agents/            # Per-phase agent docs
├── apps/web/              # Next.js (kept shell + product pages)
├── services/
│   ├── api/               # FastAPI + Celery tasks
│   ├── worker/            # Worker deps (references api)
│   └── core/              # stoa_core shared package
├── legacy/                # Archived GTM/marketing code (do not deploy)
└── supabase/migrations/   # Greenfield schema
```

## Tenancy

- **Multi-organization per user** — `memberships` is unique on `(org_id, user_id)` only; one user may belong to many orgs.
- **Active org context** — API resolves scope from `X-Org-Id` header → `user_profiles.last_active_org_id` → sole membership; ambiguous multi-org requests return `409 org_selection_required`.
- **RBAC** — four immutable **system roles** (`owner`, `admin`, `analyst`, `viewer`) plus **custom roles** with `resource:action` permissions from `stoa_core.security.permissions`.
- **Org creation** — no auto-provision trigger on signup; owners create orgs via `POST /v1/onboarding/complete` (or create-mode from org switcher).
- **Invite acceptance** — additive membership only; never deletes the invitee's other orgs.

## API surface (`/v1`)

| Area | Prefix |
|------|--------|
| Auth workflow | `/v1/auth` |
| Onboarding | `/v1/onboarding` |
| Orgs | `/v1/orgs` |
| Roles | `/v1/roles` |
| Team | `/v1/team` |
| Dashboard | `/v1/dashboard` |
| Data hub (UI) | `/data` |
| Ingestion | `/v1/ingestion` |
| Intelligence | `/v1/intelligence` (+ `/insights`) |
| Conversations | `/v1/conversations` |
| Competitive | `/v1/competitive` |
| Campaigns | `/v1/campaigns` |

## Agent orchestration

- **Phases 0–1:** Plain typed Python functions in `stoa_core` + Celery tasks.
- **Phase 3+:** LangGraph only for resumable generate→critic→revise workflows (see ADR-003).

## Definition of Done (every sub-phase)

- [ ] RLS policies + tests for new tables
- [ ] No secrets in client bundle
- [ ] CI green: ruff + pytest (+ mypy on core)
- [ ] Structured logging, idempotent/retryable jobs
- [ ] Audit log for sensitive writes
- [ ] Phase agent doc updated

## Phase docs

- [Phase 0 — Foundations](docs/agents/phase-0-foundations.md)
- [Phase 1 — Customer Intelligence](docs/agents/phase-1-customer-intelligence.md)
- [Phase 1b — Data Hub + Proactive Insights](docs/agents/phase-1b-proactive-insights.md)
- [Phase 1c — Unified Knowledge Base + Hybrid RAG](docs/agents/phase-1c-knowledge-base.md)
- [Phase 1d — Customer Data Integrations](docs/agents/phase-1d-customer-data-integrations.md)
- [Phase 2 — Competitive Intelligence](docs/agents/phase-2-competitive-intelligence.md)
- [Phase 3 — Campaign Orchestration](docs/agents/phase-3-campaign-orchestration.md)

## Common pitfalls

- Do not run expensive LLM chains on every user question — retrieve precomputed intelligence.
- Do not bypass RLS with anon client for writes — API uses service role with membership checks.
- Do not import from `legacy/` — copy patterns only.
- Set TTL on all Redis stream keys.
