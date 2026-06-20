# Integrations Service

**One-liner:** Fourteen OAuth and API connectors syncing CRM, calls, and reviews into the knowledge base.

## Why it exists

Marketing teams already have customer data in HubSpot, Gong, Salesforce, and elsewhere. Native connectors pull structured records into canonical Postgres tables and the unified KB — avoiding manual CSV exports.

## How it works

1. **Registry** — [`services/core/src/stoa_core/integrations/registry.py`](../../services/core/src/stoa_core/integrations/registry.py) registers connectors via `@register_connector` decorator on import.
2. **List providers** — `GET /v1/integrations/providers` returns `ProviderInfo` for each connector.
3. **Connect** — OAuth flow (`/connect/{provider}` → callback) or API-key connect (`POST /sources/{provider}/connect`).
4. **Credentials** — Encrypted with Fernet (`INTEGRATION_CREDENTIALS_KEY`) in `integration_connections` table.
5. **Sync** — `POST /sources/{id}/sync` enqueues `integrations.sync_source` Celery task.
6. **Worker** — `run_sync()` in `integrations/service.py`:
   - Loads connector class from registry
   - Pulls records from external API
   - Writes to `canonical_*` tables
   - Calls `ingest_knowledge()` for KB indexing
   - Extracts signals from interactions
7. **Downstream** — On success with records: chains `rebuild_icp_profile` + `precompute_insights`.

## Registered connectors

| Provider | Module | Auth type |
|----------|--------|-----------|
| hubspot | `hubspot.py` | OAuth |
| salesforce | `salesforce.py` | OAuth |
| gong | `gong.py` | OAuth |
| zendesk | `zendesk.py` | OAuth |
| google_drive | `google_drive.py` | OAuth |
| ga4 | `ga4.py` | OAuth |
| notion | `notion.py` | OAuth |
| slack | `slack.py` | OAuth |
| intercom | `intercom.py` | OAuth |
| jira | `jira.py` | OAuth |
| posthog | `posthog.py` | API key |
| csv_structured | `csv_structured.py` | File upload |
| reddit | `reddit.py` | Token |
| reviews | `reviews.py` | Apify token |

## Architecture diagram

```
User clicks Connect
       │
       ▼
OAuth redirect → callback → store encrypted creds
       │
User clicks Sync
       │
       ▼
Celery: integrations.sync_source
       │
       ├── connector.fetch_records()
       ├── write canonical_* tables
       ├── ingest_knowledge() → KB
       └── chain: rebuild_icp → precompute_insights
```

## Key code callouts

- **`BaseConnector`** — [`services/core/src/stoa_core/integrations/base.py`](../../services/core/src/stoa_core/integrations/base.py) — Abstract sync interface.
- **`run_sync()`** — [`services/core/src/stoa_core/integrations/service.py`](../../services/core/src/stoa_core/integrations/service.py) — Orchestrates pull + ingest.
- **`sync_integration_source`** — [`services/api/app/tasks/integrations.py`](../../services/api/app/tasks/integrations.py) — Celery wrapper.
- **HubSpot webhook** — `POST /v1/integrations/webhooks/hubspot` for push updates.

## Tech decisions

1. **Side-effect registration** — Importing connector modules registers them; no manual manifest file.
2. **Encrypted credentials** — Fernet symmetric encryption; key from env, never in client bundle.
3. **Same ingest path** — Integration records use `ingest_knowledge()` — one retrieval stack for all data.

## Talking points

- CSV import has dedicated detect + import endpoints for schema inference.
- Sync progress streams via SSE on `/sources/{id}/events`.
- OAuth state stored in Redis with TTL via `oauth_state.py`.
