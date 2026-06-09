# Security

## Authentication

- Google OAuth, Microsoft Azure OAuth, and email/password via Supabase Auth (`@supabase/ssr` cookies)
- Email/password confirmation emails are sent by Supabase Auth through Brevo custom SMTP
- FastAPI verifies JWT (JWKS for RS*/ES*, HS256 fallback) with strict `aud` + `iss`
- `sub` claim = `user_id` for authorization
- Next.js middleware gates `(app)` routes with `getUser()`
- Browser API calls use `/api/backend/*` BFF proxy (no JWT in client components)

## Authorization

- One org per user (`memberships.user_id` unique)
- RBAC: owner > admin > analyst > viewer
- API enforces `require_role` on writes and expensive job triggers
- RLS uses role-aware policies (`has_min_role`) — viewers are read-only via direct PostgREST
- Service role used only server-side with explicit `org_id` checks

## Secrets

| Variable | Where |
|----------|-------|
| `NEXT_PUBLIC_SUPABASE_*` | Browser only |
| `SUPABASE_SERVICE_ROLE_KEY` | API/worker + server-only Next routes (waitlist) |
| `SUPABASE_JWT_SECRET` | API only |
| `INVITE_TOKEN_PEPPER` | API only |
| Brevo SMTP credentials | Supabase Auth dashboard only |
| LLM API keys | Worker/core only |

## Input hardening

- Upload: extension + MIME + size limits, chunked read, safe storage filenames
- Paste: max size + document quota + doc_type validation
- SSRF: HTTPS-only fetch with private IP/DNS blocklist for competitive URLs
- Content sanitization against prompt-injection patterns (ingestion + Q&A)
- PII redaction on stored documents/knowledge and in structured logs

## Rate limiting

- Redis-backed per-user limits when available (upload, paste, ask, scans, campaigns, ICP/insights)

## Redis / Celery broker

- Production requires Redis password and TLS (`rediss://`) — validated at API/worker startup
- Celery accepts JSON tasks only; worker rejects unknown task names
- All tasks re-validate resource ownership from Postgres (never trust broker-supplied org IDs alone)

## PII

- `redact_pii()` on stored documents, messages, signals, snapshots, audit metadata, and SSE payloads
- `redact_pii_for_logs()` additionally masks IP addresses in application logs

## RLS testing

```bash
RUN_INTEGRATION_TESTS=1 pytest services/api/tests/test_rls_integration.py -q
```

Requires `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`.

## Audit

Sensitive writes log to `audit_log` (org_id, user_id, action, resource).

## Invites

- Invite tokens are generated once, hashed with `INVITE_TOKEN_PEPPER`, and stored only as hashes.
- Active invites expire and can be revoked.
- Invite acceptance requires a Supabase-authenticated user whose email matches the invite email.
- The one-company-per-user invariant is preserved; only empty auto-provisioned placeholder orgs may be replaced during invite acceptance.

## Deferred Guardrails

LLM prompt/output guardrails are tracked as a later security task after the core workflows stabilize.

## RLS testing

Run `services/api/tests/test_security.py` and apply migrations before verifying anon cannot write as viewer.
