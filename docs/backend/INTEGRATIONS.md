# Integrations Service

**One-liner:** Fourteen OAuth and API connectors syncing CRM, calls, and reviews into the knowledge base.

## Why it exists

Marketing teams already have customer data in HubSpot, Gong, Salesforce, and elsewhere. Native connectors pull structured records into canonical Postgres tables and the unified KB — avoiding manual CSV exports.

## How it works

1. **Registry** — [`services/core/src/stoa_core/integrations/registry.py`](../../services/core/src/stoa_core/integrations/registry.py) registers connectors via `@register_connector` decorator on import.
2. **List providers** — `GET /v1/integrations/providers` returns enriched `ProviderInfo` including `oauth_available`, `connectable`, `missing_env`, `resource_selection_mode`, and `resource_kinds`.
3. **Connect** — OAuth flow (`/connect/{provider}` → callback) or API-key connect (`POST /sources/{provider}/connect`). Dual-auth providers (Slack, Zendesk, Gong) support both paths. OAuth defers sync when `resource_selection_mode` is `required` until scope is saved.
4. **Configure access** — After connect, users pick resources via `GET /sources/{id}/resources` and `PATCH /sources/{id}/scope`. Selections live in `provider_metadata` (`channel_ids`, `property_id`, `object_types`, etc.). Sync is blocked until `scope_configured` is true.
5. **Credentials** — Encrypted with Fernet (`INTEGRATION_CREDENTIALS_KEY`) in `integration_connections` table.
6. **Sync** — `POST /sources/{id}/sync` enqueues `integrations.sync_source` Celery task. OAuth tokens refresh automatically before sync when a `refresh_token` is present.
7. **Worker** — `run_sync()` in `integrations/service.py` pulls records, writes canonical tables, ingests knowledge, and streams progress on SSE.
8. **Downstream** — On success with records: chains `rebuild_icp_profile` + `precompute_insights`.

## Registered connectors

| Provider | Module | Auth type | Notes |
|----------|--------|-----------|-------|
| hubspot | `hubspot.py` | OAuth | Reference connector + webhook |
| salesforce | `salesforce.py` | OAuth | Pagination + sandbox via `?environment=sandbox` |
| gong | `gong.py` | OAuth + API key | Basic auth fallback |
| zendesk | `zendesk.py` | OAuth + API token | Per-org subdomain on connect |
| google_drive | `google_drive.py` | OAuth + token | Shared Google OAuth app |
| ga4 | `ga4.py` | OAuth + token | Property chosen post-connect via scope editor |
| slack | `slack.py` | OAuth + bot token | Channels chosen post-connect |
| intercom | `intercom.py` | API token | Tags/teams chosen post-connect |
| notion | `notion.py` | Integration token | Pages/databases chosen post-connect |
| jira | `jira.py` | API token | Projects chosen post-connect |
| posthog | `posthog.py` | API key | Project chosen post-connect |
| csv_structured | `csv_structured.py` | File upload | Data Hub CSV panel |
| reddit | `reddit.py` | Platform | Query/subreddits in scope editor; `APIFY_API_TOKEN` server-side |
| reviews | `reviews.py` | Platform | Product/platforms in scope editor; `APIFY_API_TOKEN` server-side |

## Environment variables

| Variable | Connectors |
|----------|------------|
| `INTEGRATION_CREDENTIALS_KEY` | All (Fernet encryption) |
| `API_BASE_URL` | OAuth callback base (FastAPI) |
| `HUBSPOT_CLIENT_ID/SECRET` | HubSpot |
| `SALESFORCE_CLIENT_ID/SECRET` | Salesforce |
| `GONG_CLIENT_ID/SECRET` | Gong OAuth |
| `ZENDESK_CLIENT_ID/SECRET` | Zendesk OAuth |
| `GOOGLE_CLIENT_ID/SECRET` | GA4, Google Drive |
| `SLACK_CLIENT_ID/SECRET` | Slack OAuth |
| `APIFY_API_TOKEN` | Reviews + Reddit (platform, via Apify) |

### Google Cloud OAuth setup

1. Create a project in Google Cloud Console.
2. Enable **Google Analytics Data API**, **Google Analytics Admin API**, and **Google Drive API**.
3. Create OAuth 2.0 credentials (Web application).
4. Add redirect URI: `{API_BASE_URL}/v1/integrations/callback/ga4` (and `/google_drive` uses the same client).
5. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.

### Slack app setup

1. Create a Slack app at api.slack.com.
2. Add OAuth redirect: `{API_BASE_URL}/v1/integrations/callback/slack`.
3. Scopes: `channels:history`, `channels:read`, `groups:history`, `groups:read`.
4. Set `SLACK_CLIENT_ID` and `SLACK_CLIENT_SECRET`.

## OAuth callback UX

After OAuth, users return to `/data/integrations?connected={provider}&connection_id={id}` (with `&configure_scope=1` when scope is required). The UI shows a success toast, opens the scope editor when needed, refreshes connections, and subscribes to sync SSE after scope is saved.

## Scope API

| Endpoint | Purpose |
|----------|---------|
| `GET /v1/integrations/sources/{id}/scope` | Current selection + `scope_configured` |
| `GET /v1/integrations/sources/{id}/resources` | Discoverable resources (paginated `?cursor=`, `?q=`) — rate-limited |
| `PATCH /v1/integrations/sources/{id}/scope` | Merge scope into `provider_metadata`, audit `integration.scope_updated`, optional `sync: true` |

Deselected resources trigger KB purge by URI prefix (e.g. `slack:channel:{id}`) before re-sync.

## Key code callouts

- **`scope.py`** — `validate_scope`, `merge_scope_patch`, `removed_uri_prefixes`, `purge_knowledge_by_uri_prefixes`.
- **`resource_listers.py`** — Per-connector discoverable resource APIs.

- **`provider_capabilities.py`** — Enriches provider list for the UI (`connectable`, `oauth_available`).
- **`oauth_refresh.py`** — Shared token refresh before sync.
- **`google_oauth.py`** — Shared Google authorize/exchange/refresh.
- **`run_sync()`** — [`service.py`](../../services/core/src/stoa_core/integrations/service.py).
- **HubSpot webhook** — `POST /v1/integrations/webhooks/hubspot`.

## Tech decisions

1. **Side-effect registration** — Importing connector modules registers them; no manual manifest file.
2. **Encrypted credentials** — Fernet symmetric encryption; key from env, never in client bundle.
3. **Platform-managed enrichment** — Reddit and Reviews use Apify (`APIFY_API_TOKEN`); orgs only configure sources.
4. **Same ingest path** — Integration records use `ingest_knowledge()` — one retrieval stack for all data.
