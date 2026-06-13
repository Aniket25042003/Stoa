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
| Reddit | Server token | 3 |
| Salesforce | OAuth | 4 |
| Slack, Notion, Google Drive, Jira | API/OAuth | 4 |
| GA4, PostHog | API | 4 |

## API

- `GET /v1/integrations/providers`
- `GET /v1/integrations/connect/{provider}` — OAuth start
- `GET /v1/integrations/callback/{provider}` — OAuth callback
- `POST /v1/integrations/sources/{provider}/connect` — API key connect
- `POST /v1/integrations/sources/{id}/sync`
- `POST /v1/integrations/csv/import`
- `POST /v1/integrations/webhooks/hubspot`

## Celery

- `integrations.sync_source` → chains `rebuild_icp` + `precompute_insights`

## Env

- `INTEGRATION_CREDENTIALS_KEY` — Fernet key (required in production)
- `HUBSPOT_CLIENT_ID`, `HUBSPOT_CLIENT_SECRET`
- `GONG_CLIENT_ID`, `GONG_CLIENT_SECRET`
- `APIFY_API_TOKEN` — reviews import
- `API_BASE_URL` — OAuth callback base (FastAPI)

## Exit criteria

- [x] Migration + RLS on integration tables
- [x] HubSpot + CSV connectors
- [x] Gong, Zendesk, Intercom, Reviews connectors
- [x] Enrichment plugins (Slack, Notion, Drive, Jira, GA4, PostHog)
- [x] Data hub connections UI
- [x] Structured ICP aggregations
- [x] Intelligence dashboard explorers
