# Phase 1d — Customer Data Integrations

## Scope

- Native OAuth/API connectors in `stoa_core/integrations`
- Canonical CRM schema (`canonical_accounts`, `canonical_contacts`, `canonical_deals`, `canonical_interactions`)
- Dual-write: structured Postgres + unified KB via `ingest_knowledge`
- Data hub: connections UI, structured CSV wizard, file upload
- Intelligence: structured CRM aggregations merged into ICP rebuild

## Providers (implemented)

| Provider | Auth | Phase |
|----------|------|-------|
| HubSpot | OAuth | 1 |
| Structured CSV | Upload | 1 |
| Gong | OAuth + Basic | 2 |
| Zendesk | OAuth + API token | 3 |
| Intercom | API token | 3 |
| Reviews (G2/Capterra) | Apify | 3 |
| Reddit | Apify | 3 |
| Salesforce | OAuth | 4 |
| Slack, Notion, Google Drive, Jira | API/OAuth | 4 |
| GA4, PostHog | API | 4 |

## API

- `GET /v1/integrations/providers`
- `GET /v1/integrations/connect/{provider}` — OAuth start
- `GET /v1/integrations/callback/{provider}` — OAuth callback
- `POST /v1/integrations/sources/{provider}/connect` — API key connect
- `POST /v1/integrations/sources/{id}/sync`
- `GET /v1/integrations/sources/{id}/scope` — current resource selection
- `GET /v1/integrations/sources/{id}/resources` — discoverable resources for scope editor
- `PATCH /v1/integrations/sources/{id}/scope` — save selection; defers sync until configured
- `POST /v1/integrations/csv/import`
- `POST /v1/integrations/webhooks/hubspot`

## Celery

- `integrations.sync_source` → chains `rebuild_icp` + `precompute_insights`

## Env

- `INTEGRATION_CREDENTIALS_KEY` — Fernet key (required in production)
- `HUBSPOT_CLIENT_ID`, `HUBSPOT_CLIENT_SECRET`
- `GONG_CLIENT_ID`, `GONG_CLIENT_SECRET`
- `SALESFORCE_CLIENT_ID`, `SALESFORCE_CLIENT_SECRET`
- `ZENDESK_CLIENT_ID`, `ZENDESK_CLIENT_SECRET`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` — GA4 + Google Drive OAuth
- `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET`
- `APIFY_API_TOKEN` — reviews + Reddit import (platform, Apify)
- `API_BASE_URL` — OAuth callback base (FastAPI)

## Resource scope (post-connect pickers)

- Selections stored in `integration_connections.provider_metadata` (`channel_ids`, `property_id`, `object_types`, etc.)
- `scope_configured: true` required before sync for connectors with `resource_selection_mode: required`
- OAuth callback appends `configure_scope=1` when scope missing; UI opens scope editor
- Deselected resources purged from KB by URI prefix on scope PATCH
- Implementations: `scope.py`, `resource_listers.py`, `integration-scope-editor.tsx`

## Connector hardening gates

- [x] Data Hub connect routing — dual-auth (Slack/Zendesk/Gong), platform-managed badges, OAuth callback toasts
- [x] Google + Slack OAuth backends with shared token refresh
- [x] Salesforce SOQL pagination + token refresh; Zendesk per-org subdomain
- [x] Sync SSE on manual sync + user-facing `last_error` copy
- [x] Provider registry parity tests + `INTEGRATIONS.md` env matrix
- [x] Per-connector resource pickers + scope API + KB purge on scope change

## Exit criteria

- [x] Migration + RLS on integration tables
- [x] HubSpot + CSV connectors
- [x] Gong, Zendesk, Intercom, Reviews connectors
- [x] Enrichment plugins (Slack, Notion, Drive, Jira, GA4, PostHog)
- [x] Data hub connections UI
- [x] Structured ICP aggregations
- [x] Intelligence dashboard explorers
