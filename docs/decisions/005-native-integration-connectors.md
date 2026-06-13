# ADR-005: Native integration connectors

**Status:** Accepted

## Context

Customer Intelligence needs CRM, call, support, and review data from many SaaS providers. Unified API vendors (Merge, Nango) accelerate OAuth but add cost and limit custom normalization into our KB + canonical schema.

## Decision

Build **native Python connectors** in `stoa_core/integrations` with:

- Encrypted credentials in `integration_connections`
- Canonical entity tables (`canonical_accounts`, `canonical_contacts`, `canonical_deals`, `canonical_interactions`)
- Dual-write: structured Postgres rows + `ingest_knowledge()` text artifacts
- Celery `integrations.sync_source` for incremental sync

OAuth handled in FastAPI; secrets never exposed to the browser.

## Consequences

- Full control over sync logic, field mapping, and KB `kind` strings
- More engineering per provider; phased rollout (HubSpot → Gong → Zendesk → plugins)
- Credentials encrypted with Fernet (`INTEGRATION_CREDENTIALS_KEY`)
