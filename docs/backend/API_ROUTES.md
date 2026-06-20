# API Routes

**One-liner:** REST and SSE endpoints under `/v1`, grouped by feature with JWT auth and org-scoped RBAC.

## Why it exists

The Next.js frontend proxies authenticated requests to FastAPI. A consistent `/v1` prefix, permission checks, and rate limiting keep the API surface predictable and secure.

## Auth middleware

All `/v1/*` routes (except waitlist) require:

1. **JWT** — `Authorization: Bearer <supabase_access_token>` verified in `app/deps/auth.py`
2. **Org scope** — `X-Org-Id` header or resolved from user profile
3. **RBAC** — `require_permission(scope, "resource:action")` per route
4. **Rate limit** — Redis-backed on sensitive endpoints (`check_rate_limit`)

Production also requires `X-Stoa-Proxy-Secret` from the Next.js BFF.

---

## Health

| Method | Path | Auth | Returns |
|--------|------|------|---------|
| GET | `/health` | None | `{"status": "ok"}` |

---

## Auth workflow — `/v1/auth`

| Method | Path | Permission | Body/Params | Returns |
|--------|------|------------|-------------|---------|
| POST | `/signup` | Public | email, password, name | User + session hints |
| POST | `/resend-verification` | Public | email | Success message |
| POST | `/rate-limit-gate` | Public | — | Rate limit check |
| GET | `/session-state` | JWT | — | Email verified, onboarding status, org list |

---

## Onboarding — `/v1/onboarding`

| Method | Path | Permission | Returns |
|--------|------|------------|---------|
| GET | `/context` | JWT | Org creation context |
| GET | `/status` | JWT | Onboarding step status |
| POST | `/complete` | JWT | Creates org + owner membership |

---

## Organizations — `/v1/orgs`

| Method | Path | Permission | Returns |
|--------|------|------------|---------|
| GET | `` | JWT | List user's orgs |
| POST | `/switch` | JWT | Set active org |
| GET | `/me` | JWT | Current org details |
| PATCH | `/me` | org:write | Update org profile |
| POST | `/leave` | JWT | Leave org |
| POST | `/transfer-ownership` | owner | Transfer ownership |
| DELETE | `/me` | owner | Delete org |
| POST | `/onboarding` | — | **410 Gone** (legacy alias) |

---

## Roles — `/v1/roles`

| Method | Path | Permission | Returns |
|--------|------|------------|---------|
| GET | `/catalog` | roles:read | System + custom role catalog |
| GET | `` | roles:read | Org roles |
| POST | `` | roles:manage | Create custom role |
| PATCH | `/{role_id}` | roles:manage | Update role |
| DELETE | `/{role_id}` | roles:manage | Delete role |

---

## Team — `/v1/team`

| Method | Path | Permission | Returns |
|--------|------|------------|---------|
| GET | `/members` | team:read | Member list |
| PATCH | `/members/{id}` | team:manage | Update member role |
| DELETE | `/members/{id}` | team:manage | Remove member |
| GET | `/invites` | team:read | Pending invites |
| POST | `/invites` | team:manage | Send invite |
| POST | `/invites/{id}/revoke` | team:manage | Revoke invite |
| POST | `/invites/accept` | JWT | Accept invite token |

---

## Dashboard — `/v1/dashboard`

| Method | Path | Permission | Returns |
|--------|------|------------|---------|
| GET | `/summary` | intelligence:read | Counts, CRM stats, completeness |

---

## Ingestion — `/v1/ingestion`

| Method | Path | Permission | Returns |
|--------|------|------------|---------|
| GET | `/sources` | data_sources:read | Data source list |
| POST | `/upload` | data_sources:write | Job ID (multipart) |
| POST | `/paste` | data_sources:write | Job ID (JSON body) |
| GET | `/jobs/{job_id}` | data_sources:read | Job status |

---

## Integrations — `/v1/integrations`

| Method | Path | Permission | Returns |
|--------|------|------------|---------|
| GET | `/providers` | data_sources:read | Available connectors |
| GET | `/sources` | data_sources:read | Connected sources |
| GET | `/connect/{provider}` | data_sources:write | OAuth redirect URL |
| GET | `/callback/{provider}` | Public | OAuth callback |
| POST | `/sources/{provider}/connect` | data_sources:write | API-key connect |
| POST | `/sources/{id}/sync` | data_sources:write | Enqueue sync task |
| DELETE | `/sources/{id}` | data_sources:write | Disconnect |
| GET | `/sources/{id}/runs` | data_sources:read | Sync run history |
| POST | `/csv/detect` | data_sources:write | CSV schema detection |
| POST | `/csv/import` | data_sources:write | CSV import |
| GET | `/sources/{id}/events` | data_sources:read | SSE sync progress |
| POST | `/webhooks/hubspot` | Public (signed) | HubSpot webhook |

---

## Intelligence — `/v1/intelligence`

| Method | Path | Permission | Returns |
|--------|------|------------|---------|
| GET | `/signals` | intelligence:read | Extracted signals |
| GET | `/icp` | intelligence:read | Latest ICP profile |
| POST | `/icp/rebuild` | intelligence:write | Enqueue ICP rebuild |
| GET | `/insights` | intelligence:read | Precomputed insights |
| POST | `/insights/refresh` | intelligence:write | Enqueue precompute |
| GET | `/documents` | intelligence:read | Document list |
| GET | `/documents/{id}` | intelligence:read | Document detail |
| PATCH | `/documents/{id}` | intelligence:write | Update document |
| DELETE | `/documents/{id}` | intelligence:write | Delete document |

---

## Conversations — `/v1/conversations`

| Method | Path | Permission | Returns |
|--------|------|------------|---------|
| GET | `` | conversations:read | Conversation list |
| POST | `/ask` | conversations:ask | `{conversation_id, status: processing}` |
| GET | `/{id}` | conversations:read | Conversation + messages |
| GET | `/{id}/events` | conversations:read | **SSE** answer stream |

Rate limit: `check_rate_limit` on `/ask`.

---

## Competitive — `/v1/competitive`

| Method | Path | Permission | Returns |
|--------|------|------------|---------|
| GET | `/competitors` | competitive:read | Competitor list |
| POST | `/competitors` | competitive:write | Add competitor |
| PATCH | `/competitors/{id}` | competitive:write | Update competitor |
| DELETE | `/competitors/{id}` | competitive:write | Delete competitor |
| GET | `/alerts` | competitive:read | Alert list |
| POST | `/competitors/{id}/scan` | competitive:write | Enqueue monitor task |

---

## Campaigns — `/v1/campaigns`

| Method | Path | Permission | Returns |
|--------|------|------------|---------|
| GET | `` | campaigns:read | Campaign list |
| POST | `` | campaigns:write | Create + enqueue generation |
| GET | `/{id}` | campaigns:read | Campaign detail + assets |

---

## Waitlist — `/v1/waitlist`

| Method | Path | Auth | Returns |
|--------|------|------|---------|
| POST | `` | Public | Join waitlist |

---

## Key code callouts

- **Router registration** — [`services/api/app/main.py`](../../services/api/app/main.py)
- **Org scope** — [`services/api/app/deps/org_scope.py`](../../services/api/app/deps/org_scope.py)
- **Rate limiting** — [`services/api/app/deps/rate_limit.py`](../../services/api/app/deps/rate_limit.py)
- **Audit log** — Sensitive writes call `write_audit()` in router handlers

## Talking points

- No `/v1/runs` or `/v1/marketing` — legacy endpoints removed; frontend redirects stub routes.
- Insights live under `/v1/intelligence/insights`, not a separate router.
- SSE endpoints stream from Redis via `read_events_since()` in conversations and integrations routers.
