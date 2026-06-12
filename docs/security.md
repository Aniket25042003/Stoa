# Security

## Authentication

- Google OAuth, Microsoft Azure OAuth, and email/password via Supabase Auth (`@supabase/ssr` cookies)
- Email/password confirmation emails are sent by Supabase Auth through Brevo custom SMTP
- FastAPI verifies JWT (JWKS for RS*/ES*, HS256 fallback) with strict `aud` + `iss`
- `sub` claim = `user_id` for authorization
- Next.js middleware gates `(app)` routes with `getUser()`
- Browser API calls use `/api/backend/*` BFF proxy (no JWT in client components)

## Authorization

- **Multi-org tenancy** — users may belong to many organizations; active scope from `X-Org-Id` + membership validation
- **IAM-style RBAC** — system roles (`owner`, `admin`, `analyst`, `viewer`) plus custom roles with `resource:action` permissions
- **Permission boundary** — non-owner holders of `roles:manage` can only grant permissions ⊆ their own
- **Owner-reserved** — `org:delete`, `org:transfer_ownership` never grantable; owner implicitly holds all permissions
- API enforces `require_permission` on writes and expensive job triggers; `require_role` only for owner-reserved actions
- RLS uses `is_org_member` / `has_permission_in_org` — coarse table access; fine-grained reads enforced in API via org scope
- Service role used only server-side with explicit `(user_id, org_id)` membership checks

## Secrets

| Variable | Where |
|----------|-------|
| `NEXT_PUBLIC_SUPABASE_*` | Browser only |
| `SUPABASE_SERVICE_ROLE_KEY` | API/worker only (never in the web app) |
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
- Public auth/waitlist endpoints rate limit by trusted client IP plus email (Redis required; fail closed)
- Next.js BFF sets `X-Stoa-Client-IP` + `X-Stoa-Proxy-Secret` when `INTERNAL_PROXY_SECRET` is configured

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
- **Additive membership** — accepting an invite adds (or syncs) a membership row; other org memberships are never deleted.
- Invites may specify `role_id` (system or custom) and `profile_hints` for shortened invitee onboarding.
- Deleted custom roles referenced by pending invites degrade to viewer on acceptance.

## Email verification

- Product API routes require a verified email for password signups (`403` until confirmed)
- OAuth users are treated as verified by provider
- `/v1/auth/session-state` remains available for the verify-email polling flow

## Secret rotation (pre-launch)

1. Rotate `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, and `SUPABASE_ANON_KEY` in Supabase dashboard
2. Update Render/Vercel env vars and redeploy API + web
3. Set a unique `INVITE_TOKEN_PEPPER` and `INTERNAL_PROXY_SECRET` (never commit)
4. Revoke old keys after deploy health checks pass

## Prompt injection / PII

- Ingestion and Q&A use best-effort regex sanitization and `redact_pii()` — not a substitute for model-level guardrails
- Deferred: dedicated LLM input/output policy layer after core workflows stabilize

## RLS testing

Run `services/api/tests/test_security.py` and apply migrations before verifying anon cannot write as viewer.
