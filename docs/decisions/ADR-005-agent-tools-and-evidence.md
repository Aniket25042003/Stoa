# ADR-005: Agent tools and evidence cache

## Status

Accepted

## Context

The unified GTM agent initially exposed six dashboard tools that read pre-synced Postgres only. Users often need fresher data than scheduled connector syncs provide, and the agent could not run additional KB searches mid-turn with refined queries.

## Decision

1. **Tiered tool catalog** in `stoa_core.agent.tools`:
   - Tier 1: `search_workspace_memory`, `get_workspace_freshness`
   - Tier 2: `search_connected_sources` via connector `agent_search()`
   - Tier 3: `refresh_connected_source`, `refresh_precomputed_insights`, `refresh_competitor_intel` (async Celery)
   - Tier 4: `lookup_canonical_records`
   - Tier 5: `search_public_web` (guardrailed, optional)

2. **Evidence pipeline** (`stoa_core.agent.evidence`):
   - Sanitize all tool-sourced text (`redact_pii` + `sanitize_user_content`)
   - Redis conversation cache keyed by org + conversation + query hash
   - In-process turn accumulator for dedupe
   - End-of-turn `persist_turn_evidence()` → `ingest_knowledge(kind=agent_search_evidence)`

3. **Connector contract**: optional `BaseConnector.agent_search()` with normalized `AgentSearchHit`; orchestrated by `integrations/agent_search.run_agent_search()`.

4. **Rate limits**: per-org Redis counters for live search (hourly), refresh (hourly), web search (daily).

## Consequences

- Live connector calls are opt-in and capped; default path remains retrieval + synthesis.
- KB grows `agent_search_evidence` chunks so repeat questions need fewer live searches.
- Celery enqueue for refresh lives in `agent/refresh_enqueue.py` with lazy `app.tasks` imports (worker runtime only).
- Route classifier keywords expanded for freshness/live-search intents.

## Alternatives considered

- **Always live API**: rejected (cost, latency, rate limits).
- **No KB persist**: rejected; user requirement to learn from searches across conversations.
