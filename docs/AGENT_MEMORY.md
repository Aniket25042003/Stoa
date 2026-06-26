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
| KB version counter | Redis `stoa:kb:version:{org}` | Bumped on ingest |
| Enrichment job status | `enrichment_jobs` table | Permanent audit trail |
| Company web research | `knowledge_chunks` (kind=company_web_research) | On onboarding / profile update |
| Competitive research | `knowledge_chunks` (kind=competitive_snapshot, competitive_research) | On competitor add / scheduled rescan |
| Conversation checkpoints | `knowledge_chunks` (kind=conversation_memory) | Every N user turns in a thread |

### How context reaches the LLM

1. **Precomputed path** — Dashboard and intelligence pages read `precomputed_insights` directly (no LLM call).
2. **Ad-hoc Q&A path**:
   - User message saved to `messages`
   - Celery task `answer_intelligence_question` runs
   - `retrieve_context(org_id, question, kinds=INTELLIGENCE_KINDS)` fetches ranked chunks
   - `answer_question(question, context)` builds prompt with up to 30 context lines
   - Assistant message inserted into `messages`
   - SSE event published for realtime UI update

### Context window management

There is **no conversation history summarization or sliding window** in the active stack. Context management happens at retrieval time:

1. **Hybrid search** returns ~40 candidates
2. **Rerank + MMR** reduces to ~12 diverse chunks
3. **Token budget** (`RETRIEVAL_TOKEN_BUDGET=2000`) trims total tokens
4. **Answer prompt** uses top 30 context items max

Prior conversation messages are stored but **not** injected into the RAG answer prompt today — each question is answered from retrieved KB context only.

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
