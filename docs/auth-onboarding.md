# Auth + Onboarding

## Providers

Stoa uses Supabase Auth for sessions and JWTs. The app supports:

- Google OAuth
- Microsoft Azure OAuth
- Email/password with Supabase email confirmation

For Azure, configure the Supabase Azure provider and the Microsoft Entra app with the Supabase callback URL. Request the `email` scope and add the optional `xms_edov` claim in Entra where possible.

## Brevo SMTP

Email/password verification is delivered by Supabase Auth through Brevo custom SMTP. Configure this in the Supabase dashboard under Authentication -> SMTP:

- Host: `smtp-relay.brevo.com`
- Port: `587` (STARTTLS) or `465` (SSL)
- Username: your Brevo SMTP login email (not the API key)
- Password: Brevo **SMTP key** (SMTP & API -> SMTP keys — not the REST API key)
- Sender email/name from a verified Brevo sender/domain
- Enable **Confirm email** under Authentication -> Providers -> Email

Supabase sends mail from **Supabase cloud IPs**, not your laptop. Allowing your local IP in Brevo only helps local SMTP tests; production delivery depends on Brevo accepting Supabase relay credentials.

### If verification emails never arrive

1. Supabase Dashboard -> Authentication -> **Logs** (look for SMTP/mailer errors)
2. Brevo -> Transactional -> **Email logs** and **Blocked contacts**
3. Supabase -> Authentication -> **URL configuration**:
   - Site URL: `http://localhost:3000` (dev)
   - Redirect URLs: `http://localhost:3000/auth/callback`, `http://localhost:3001/auth/callback` if you use another port
4. Supabase -> Authentication -> **Rate limits** (signup emails default to a low hourly cap)
5. API `.env` must include `SUPABASE_ANON_KEY` (same as web anon key) — resend uses the public Auth API

Supabase still applies Auth email rate limits even with custom SMTP. Adjust Auth rate limits in Supabase for production after confirming sender reputation and abuse controls.

## Multi-Org Tenancy Model

- Supabase Auth owns identity.
- `user_profiles` stores per-user onboarding metadata and `last_active_org_id`.
- `organizations` is the company entity; `organizations.onboarding_completed_at` tracks org-level setup.
- `memberships` allows **multiple rows per user** (unique on `org_id + user_id`).
- `org_roles` stores system + custom IAM-style roles with `permissions text[]`.
- `org_invites` stores hashed tokens, `role_id`, and optional `profile_hints` for invitee onboarding.

Invite emails are attempted through Supabase Auth admin invites so delivery uses the configured Brevo SMTP sender. The API also returns a fallback invite link for development/manual sharing.

**Invite acceptance is additive** — joining Company B does not delete or replace membership in Company A.

## Post-Auth Routing

After OAuth callback or email sign-in:

1. `/v1/auth/session-state` repairs/loads `user_profiles` and memberships.
2. Email/password users without Supabase confirmation go to `/verify-email`.
3. Invite links go to `/invite/[token]`.
4. Incomplete users go to `/onboarding` (dedicated route group — **no product nav**).
5. Ready users land on `/dashboard` or the requested `next` path.

The `(app)` layout performs a **server-side** redirect to `/onboarding` when `needs_onboarding` is true. Product API routes return `403 onboarding_required` as defense in depth.

## Dedicated Onboarding Workflow

Route group: `apps/web/src/app/(onboarding)/` — minimal shell (brand, progress, sign out).

### Context API

`GET /v1/onboarding/context` returns:

- `mode`: `owner_setup` | `invitee_profile` | `complete`
- `memberships`, `prefilled` fields (email domain, invite `profile_hints`)
- `required_steps` for the linear wizard

### Atomic completion

`POST /v1/onboarding/complete` — single transactional write (no per-step persistence):

1. Upsert `user_profiles` + `onboarding_completed_at`
2. Owner path: create org, seed 4 system roles, owner membership, set `last_active_org_id`
3. Ingest `kind=company_profile` into knowledge base
4. Optional seed document + teammate invites with `role_id` and `profile_hints`
5. Audit events

Draft state lives in React + `sessionStorage` until completion.

### Processing step

`/onboarding/processing` polls `GET /v1/onboarding/status` until company profile knowledge is indexed, then redirects to `/dashboard`.

## Active Organization

- Browser cookie `stoa-active-org` set by `POST /api/orgs/switch`
- BFF proxy and server `apiFetch` forward `X-Org-Id` to FastAPI
- Org switcher lists `GET /v1/orgs`; users can create a new org via `/onboarding?mode=create`

## Manual QA

- New email signup -> verify -> gated onboarding (no nav) -> complete -> processing -> dashboard
- OAuth new user -> same flow; company name prefilled from email domain
- Owner of Company A accepts invite to Company B -> two memberships; switcher shows both; Company A intact
- Invite-only new user -> short profile wizard -> inviter's org; can create own org later
- Owner creates custom role -> member permissions isolated per org
- Forged `X-Org-Id` for non-member org -> 403
- Multi-org user without header/cookie -> `409 org_selection_required`
