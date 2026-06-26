# Agent Memory

**One-liner:** Postgres for conversations and precomputed intelligence; Redis for SSE and retrieval cache.

## Why it exists

The platform does not run multi-agent LangGraph loops on each request. Instead, "memory" means persisted conversation history, precomputed insights, and cached retrieval results — giving the LLM enough context without re-deriving everything per question.

## How it works

### What gets stored

| Data | Where | TTL / lifecycle |
|------|-------|-----------------|
| Conversation title + metadata | `conversations` table | Permanent |
| User + assistant messages | `messages` table | Permanent |
| Precomputed insight Q&A | `precomputed_insights` table | Refreshed on ingest/sync |
| ICP profiles (versioned) | `icp_profiles` table | New version on rebuild |
| Knowledge chunks + embeddings | `knowledge_chunks` table | Updated on re-ingest |
| Extracted signals | `intelligence` table | Per document chunk |
| Generated content metadata | `content_assets` table | Permanent |
| Content asset KB entries | `knowledge_chunks` (kind=content_asset) | Permanent |
| SSE progress events | Redis streams `stoa:{scope}:{id}:events` | 72h TTL, 10k maxlen |
| Query embedding cache | Redis `stoa:kb:qemb:{org}:{hash}` | 1800s TTL |
| Retrieval result cache | Redis `stoa:kb:result:{org}:{version}:{hash}` | 3600s TTL |
| Query rewrite cache | Redis `stoa:kb:rewrite:{org}:{version}:{hash}` | 3600s TTL |
| RAG answer cache | Redis `stoa:kb:answer:{org}:{version}:{hash}` | 1800s TTL |
| Ask idempotency | Redis `stoa:ask:idempotency:{org}:{user}:{key}` | 24h TTL |
| KB version counter | Redis `stoa:kb:version:{org}` | Bumped on ingest |
| Enrichment job status | `enrichment_jobs` table | Permanent audit trail |
| Company web research | `knowledge_chunks` (kind=company_web_research) | On onboarding / profile update |
| Competitive research | `knowledge_chunks` (kind=competitive_snapshot, competitive_research) | On competitor add / scheduled rescan |
| Conversation checkpoints | `knowledge_chunks` (kind=conversation_memory) | Every N user turns in a thread |
| Agent search evidence | `knowledge_chunks` (kind=agent_search_evidence) | Persisted end-of-turn from live/canonical/web tool hits |
| Conversation evidence cache | Redis `stoa:agent:evidence:{org}:{conversation}:{hash}` | `agent_evidence_conversation_ttl_seconds` (default 72h) |

### How context reaches the LLM

1. **Precomputed path** — Dashboard and intelligence pages read `precomputed_insights` directly (no LLM call).
2. **Ad-hoc Q&A path**:
   - User message saved to `messages`
   - Celery task `answer_intelligence_question` runs (idempotent per user message)
   - `classify_agent_route()` chooses `rag_only` vs `tools`
   - `retrieve_context_prepared()` may rewrite the query, then fetches ranked chunks
   - RAG-only: `answer_question()` with cached answers when applicable
   - Tools route: LangChain agent with tiered tools (`build_agent_tools`: memory, live search, refresh, canonical, dashboard, optional web)
   - End of turn: `persist_turn_evidence()` writes sanitized connector/web/canonical hits to KB
   - Assistant message inserted into `messages`
   - SSE event published for realtime UI update

### Context window management

The unified agent uses **short-term chat history** in the LangChain prompt (recent messages + compacted older turns). Long-term memory comes from `retrieve_context_prepared()`:

1. Optional cheap query rewrite for short / pronoun-heavy questions
2. Hybrid search returns ~40 candidates per search query (multi-query merge when rewritten)
3. **Rerank + MMR** reduces to ~12 diverse chunks
4. **Token budget** (`RETRIEVAL_TOKEN_BUDGET=2000`) trims total tokens
5. **Thread filter** on `conversation_memory` chunks when `conversation_id` is set
6. Conversation checkpoints every 6 user turns via `maybe_checkpoint_conversation()`

### Agent evidence layer

Search tools (`search_workspace_memory`, `search_connected_sources`, `lookup_canonical_records`, `search_public_web`) share `stoa_core.agent.evidence`:

1. **Cache read** — identical query in the same conversation hits Redis before external I/O.
2. **Sanitize** — `redact_pii` + `sanitize_user_content` on all cached/persisted text.
3. **Turn accumulator** — dedupes hits by URI during one `run_unified_agent_turn`.
4. **Persist** — after the answer, up to `agent_evidence_max_persist_per_turn` hits ingest as `agent_search_evidence` (URI `agent_evidence:{provider}:{id}`) for cross-thread retrieval.

Prefer KB evidence newer than connector `last_sync_at` before live search; use `get_workspace_freshness` when unsure.

## Architecture diagram

```
┌─────────────────────────────────────────────────┐
│  Long-term (Postgres)                            │
│  conversations → messages                       │
│  precomputed_insights, icp_profiles             │
│  knowledge_items → knowledge_chunks (pgvector)  │
│  intelligence (structured signals)              │
└────────────────────┬────────────────────────────┘
                     │
         User asks question
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  Retrieval (with Redis cache)                   │
│  embed query → match_knowledge → rerank → MMR   │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  Single LLM call (invoke_text, task=synthesize) │
│  System prompt + retrieved context + question │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
              messages table + SSE event
```

## Key code callouts

- **`answer_intelligence_question`** — [`services/api/app/tasks/intelligence.py`](../services/api/app/tasks/intelligence.py) — Celery task orchestrating retrieve + answer.
- **`run_unified_agent_turn()`** — [`services/core/src/stoa_core/agent/unified_agent.py`](../services/core/src/stoa_core/agent/unified_agent.py) — Route classification, prepared retrieval, tools vs RAG-only.
- **`retrieve_context_prepared()`** — [`services/core/src/stoa_core/rag/query_prepare.py`](../services/core/src/stoa_core/rag/query_prepare.py) — Query rewrite + multi-query retrieval.
- **`retrieve_context()`** — [`services/core/src/stoa_core/rag/retrieve.py`](../services/core/src/stoa_core/rag/retrieve.py) — Cached hybrid retrieval.
- **`publish_event()`** — [`services/core/src/stoa_core/redis/client.py`](../services/core/src/stoa_core/redis/client.py) — Redis stream SSE events.
- **`precompute_answers()`** — [`services/core/src/stoa_core/insights/common.py`](../services/core/src/stoa_core/insights/common.py) — Background insight generation.

## Tech decisions

1. **Retrieve + synthesize, not agent memory** — No Redis list of agent thoughts; evidence comes from pre-ingested KB.
2. **KB version invalidation** — Cache keys include KB version so re-ingest automatically busts stale retrieval results.
3. **PII redaction before storage** — `redact_pii()` applied to messages and context before LLM calls.

## Talking points

- Legacy GTM agent memory (Redis `gtm:run:*:memory` lists) lives in `legacy/` — not used by active platform.
- Precomputed insights are the "proactive memory" — dashboard reads them without LLM latency.
- SSE streams have explicit TTL (72h) per AGENTS.md doctrine.
