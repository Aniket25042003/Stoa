# Phase 1e — Agent tools expansion

## Goal

Extend the unified GTM agent with tiered tools: mid-turn KB search, live connector queries, freshness-aware refresh, canonical lookups, and an evidence cache that persists sanitized search hits into the KB.

## Deliverables

| Area | Location |
|------|----------|
| Tool registry | `services/core/src/stoa_core/agent/tools/` |
| Evidence pipeline | `services/core/src/stoa_core/agent/evidence.py` |
| Live search orchestrator | `services/core/src/stoa_core/integrations/agent_search.py` |
| Connector `agent_search` | HubSpot, Salesforce, GA4, PostHog, Zendesk, Gong, Slack, Notion, Google Drive |
| Agent integration | `unified_agent.py` → `build_agent_tools()` + `persist_turn_evidence()` |
| Config | `agent_evidence_*`, `agent_live_search_*`, `agent_refresh_*`, `agent_web_search_*` |
| ADR | `docs/decisions/ADR-005-agent-tools-and-evidence.md` |

## Tool tiers

### Tier 1 — Memory

- `search_workspace_memory` — additional `retrieve_context_prepared()` mid-turn
- `get_workspace_freshness` — sync times, stale insights, KB version

### Tier 2 — Live search

- `search_connected_sources(provider, query, entity_type?)` — `run_agent_search()` + evidence cache

### Tier 3 — Refresh (async)

- `refresh_connected_source` → `integrations.sync_source`
- `refresh_precomputed_insights` → `intelligence.precompute_insights`
- `refresh_competitor_intel` → `competitive.monitor` + `enrichment.enrich_competitor`

### Tier 4 — Canonical lookup

- `lookup_canonical_records` — SQL on `canonical_*` tables

### Tier 5 — Web (guardrailed)

- `search_public_web` — wraps `research_web()` when not disabled

## Evidence flow

1. Tool checks Redis conversation cache
2. On miss: run search → sanitize → store Redis + turn accumulator
3. End of turn: persist connector/web/canonical hits (cap per turn) as `agent_search_evidence` chunks

## Definition of Done

- [x] Tool registry + evidence scaffold + Tier 1 tools
- [x] `AgentSearchHit`, `run_agent_search`, CRM agent_search
- [x] `search_connected_sources` with rate limits and tests
- [x] GA4/PostHog/Zendesk/Gong + refresh tools
- [x] Slack/Notion/Drive + `lookup_canonical_records`
- [x] ADR-005, phase doc, `AGENT_MEMORY.md` evidence section
- [x] Celery allowlist includes enrichment/integration beat tasks
- [x] Tiered routing (`resolve_agent_route`, precomputed enrichment, bounded agent) — ADR-006

## Tests

- `tests/test_agent_evidence.py`
- `tests/test_agent_search.py`
- `tests/test_agent_tools_registry.py`
- `tests/test_route_resolver.py`
- `tests/test_bounded_agent.py`
