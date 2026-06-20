# Testing

**One-liner:** Python pytest for core and API; ESLint for web; no frontend unit tests yet.

## Why it exists

Backend business logic (RAG, permissions, sanitization, integrations) needs automated verification. CI runs on every push to `main`/`master` and on pull requests.

## Test organization

### Core (`services/core/tests/`) — 13 test files, 56 tests

| File | Covers |
|------|--------|
| `test_rag_ingest.py` | `ingest_knowledge()` idempotency, chunking, embedding |
| `test_rag_retrieve.py` | `retrieve_context()` pipeline, caching |
| `test_rerank.py` | Cohere/LLM/BM25 rerank cascade |
| `test_chunk.py` | Text chunking boundaries and overlap |
| `test_extract_eval.py` | Signal extraction returns list (no LLM) |
| `test_insights.py` | Precomputed insight generation |
| `test_integrations.py` | Connector registry, sync helpers |
| `test_permissions.py` | RBAC permission checks |
| `test_pii.py` | PII redaction patterns |
| `test_sanitize.py` | User content sanitization |
| `test_ssrf.py` | URL validation for competitive fetch |
| `test_completeness.py` | Org profile completeness scoring |
| `test_redis_security.py` | Redis TLS validation |

### API (`services/api/tests/`) — 14 test files, 33 passed + 5 skipped

| File | Covers |
|------|--------|
| `test_auth.py` | JWT verification (HS256, audience) |
| `test_security.py` | Auth edge cases |
| `test_health.py` | `/health` endpoint |
| `test_dashboard.py` | Dashboard summary endpoint |
| `test_document_delete.py` | Document deletion + audit |
| `test_competitive_competitors.py` | Competitor CRUD |
| `test_legacy_org_filter.py` | Legacy stub org filtering |
| `test_rate_limit.py` | Redis rate limiting |
| `test_task_context.py` | Celery task allowlist + org validation |
| `test_redis_security.py` | Redis TLS in API context |
| `test_rls_integration.py` | **Integration** — live Supabase RLS (skipped unless `RUN_INTEGRATION_TESTS=1`) |

### Web (`apps/web/`) — no tests

- No `*.test.ts` or `*.spec.ts` files
- CI runs `pnpm lint:web` + `pnpm audit` only

### Legacy (`legacy/services/api/tests/`) — not in CI

9 archived test files for old GTM/marketing API.

## How to run locally

```bash
# Core
cd services/core
pip install -e ".[dev]"
ruff check src tests
pytest -q

# API
cd services/api
pip install -r requirements-dev.txt
pytest -q

# Integration tests (requires live Supabase)
RUN_INTEGRATION_TESTS=1 pytest -q tests/test_rls_integration.py

# Web lint
pnpm lint:web
```

## CI pipeline

[`.github/workflows/ci.yml`](../.github/workflows/ci.yml):

| Job | Steps |
|-----|-------|
| `web` | pnpm install, lint, audit |
| `core` | pip install, pip-audit, ruff, pytest |
| `api` | pip install, pip-audit, pytest |
| `secrets` | gitleaks scan |

Note: mypy is in core dev deps but **not** run in CI today.

## Architecture diagram

```
Developer push/PR
       │
       ▼
GitHub Actions CI
  ├── web: eslint + audit
  ├── core: ruff + pytest (56 tests)
  ├── api: pytest (33 tests)
  └── secrets: gitleaks
```

## Coverage gaps (honest assessment)

| Area | Status |
|------|--------|
| Frontend components | No unit or E2E tests |
| API route integration | Mostly unit tests with mocks; few full HTTP tests |
| Celery tasks | Tested indirectly via core; no worker integration tests |
| LLM calls | Mocked or skipped (extract eval placeholder) |
| SSE streaming | Not tested |
| Multi-org RBAC flows | Partial; RLS integration test exists but skipped by default |
| Playwright/Cypress E2E | Not configured |

## Key code callouts

- **`services/core/pytest.ini`** — pytest config in pyproject.toml
- **`services/api/pytest.ini`** — `integration` marker for RLS tests
- **`services/api/tests/conftest.py`** — Fixtures, integration test gate

## Tech decisions

1. **Core-first testing** — Business logic tested in `stoa_core` without HTTP overhead.
2. **Integration tests opt-in** — RLS tests require live Supabase credentials; skipped in CI by default.
3. **No frontend test framework yet** — Product is early; lint + manual QA for UI.

## Talking points

- 56 core + 33 API unit tests give confidence in RAG pipeline and auth.
- `test_extract_eval.py` is a Phase 1.6 placeholder — doesn't call real LLM.
- Adding Playwright for critical flows (onboarding, ask question) would be a natural next step.
