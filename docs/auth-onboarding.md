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

## App-Owned Company Model

- Supabase Auth owns identity.
- `user_profiles` stores lightweight app profile/onboarding metadata.
- `organizations` remains the company entity.
- `memberships.user_id` stays unique: one company per user.
- `org_invites` stores hashed app invite tokens and RBAC role to grant.

Invite emails are attempted through Supabase Auth admin invites so delivery uses the configured Brevo SMTP sender. The API also returns a fallback invite link for development/manual sharing.

## Post-Auth Routing

After OAuth callback or email sign-in:

1. `/v1/auth/session-state` repairs/loads `user_profiles`.
2. Email/password users without Supabase confirmation go to `/verify-email`.
3. Invite links go to `/invite/[token]`.
4. Incomplete users go to `/onboarding`.
5. Ready users land on `/dashboard` or the requested `next` path.

## Guided Onboarding

Onboarding collects:

- User role / job context
- Company basics
- ICP and market context
- Optional seed notes/documents
- Optional teammate invites

Company context is ingested immediately into the unified knowledge base as `kind=company_profile`.

## Manual QA

- Google login -> onboarding -> dashboard
- Azure login -> onboarding -> dashboard
- Email signup -> Supabase/Brevo verification email -> callback -> onboarding -> dashboard
- Unverified email sign-in -> `/verify-email`
- Owner creates invite -> invitee signs in with matching email -> same company
- Existing real-company user cannot accept another company invite
