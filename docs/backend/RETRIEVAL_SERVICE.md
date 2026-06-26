# Retrieval Service

**One-liner:** Hybrid vector + full-text search fused by RRF, reranked, deduplicated, and token-budgeted.

## Why it exists

User questions need relevant evidence from thousands of ingested chunks. Pure vector search misses keyword matches; pure full-text misses semantic similarity. Hybrid retrieval with reranking gives precise, diverse, budget-constrained context for a single LLM synthesis call.

## How it works

### Pipeline: query in → context list out

0. **Query preparation (agent path)** — `prepare_query()` / `retrieve_context_prepared()` may rewrite short or pronoun-heavy questions via cheap LLM (`query_rewrite` tier), then run multi-query retrieval and merge results.
1. **Normalize query** — `_normalize_query()` lowercases and collapses whitespace.
2. **Check Redis cache** — `get_cached_retrieval_result()` keyed by org + KB version + query hash (+ optional conversation scope).
3. **Embed query** — `embed_query()` (cached separately via `get_cached_query_embedding()`). Raises `EmbeddingUnavailableError` instead of returning a zero vector.
4. **Hybrid search RPC** — `_match_knowledge_rpc()` calls Postgres function `match_knowledge`:
   - Vector hits: cosine distance on `knowledge_chunks.embedding` (HNSW index)
   - Text hits: `tsvector` full-text on `content_tsv`
   - Fusion: Reciprocal Rank Fusion (RRF) with `p_rrf_k` (default 60)
   - Optional kind filter (e.g. `document`, `icp_profile`, `competitive_snapshot`)
5. **Similarity floor** — `_filter_low_vector_similarity()` drops weak vector-only hits when `RETRIEVAL_MIN_SIMILARITY` > 0.
6. **Thread-scoped memory** — `_filter_conversation_memory()` keeps `conversation_memory` chunks for the active thread only when `conversation_id` is provided.
7. **Rerank** — `rerank_candidates()` cascade:
   - Cohere `rerank-v3.5` (if `COHERE_API_KEY` set)
   - Vertex batch LLM rerank (JSON ranked indices)
   - BM25 fallback (no ML required)
8. **MMR dedup** — `_mmr_dedup()` reduces near-duplicate chunks (λ=0.7).
9. **Token budget** — `_apply_token_budget()` trims to `RETRIEVAL_TOKEN_BUDGET` (default 2000 tokens).
10. **Format context** — `_to_context_items()` produces refs like `kb:document:{item_id}:{chunk_id}`.
11. **Cache result** — `cache_retrieval_result()` in Redis (TTL 3600s, invalidated on KB version bump).

Additional caches (KB-version keyed): query rewrite (`stoa:kb:rewrite:*`), final RAG answers (`stoa:kb:answer:*`).

## Architecture diagram

```
Query string
    │
    ├─► embed_query() ──► query embedding
    │
    ▼
match_knowledge RPC (Postgres)
    ├── vector_hits (HNSW halfvec cosine)
    ├── text_hits (GIN tsvector)
    └── RRF fusion → candidates (k=40)
            │
            ▼
    rerank_candidates()
    ├── Cohere rerank-v3.5
    ├── Vertex LLM batch rerank
    └── BM25 fallback
            │
            ▼
    MMR dedup → token budget → final_k (12)
            │
            ▼
    list[{ref, text, score, kind, ...}]
```

## Key code callouts

- **`retrieve_context()`** — [`services/core/src/stoa_core/rag/retrieve.py`](../../services/core/src/stoa_core/rag/retrieve.py) — Main entry; all features call this.
- **`retrieve_context_prepared()`** — [`services/core/src/stoa_core/rag/query_prepare.py`](../../services/core/src/stoa_core/rag/query_prepare.py) — Query rewrite + multi-query merge for agent turns.
- **`match_knowledge`** — [`supabase/migrations/20260703000000_knowledge_base.sql`](../../supabase/migrations/20260703000000_knowledge_base.sql) — SQL RPC doing vector + FTS + RRF in one query.
- **`rerank_candidates()`** — [`services/core/src/stoa_core/rag/rerank.py`](../../services/core/src/stoa_core/rag/rerank.py) — Three-tier rerank cascade.
- **`cache.py`** — KB version invalidates stale retrieval caches on ingest.

## Configurable parameters

| Setting | Default | Purpose |
|---------|---------|---------|
| `RETRIEVAL_CANDIDATE_K` | 40 | Initial hybrid search pool |
| `RETRIEVAL_FINAL_K` | 12 | Max chunks returned |
| `RETRIEVAL_TOKEN_BUDGET` | 2000 | Total token cap for context |
| `RETRIEVAL_RRF_K` | 60 | RRF smoothing constant |
| `RETRIEVAL_MIN_SIMILARITY` | 0.0 | Vector-only hit floor (rank proxy) |
| `KB_REWRITE_CACHE_TTL_SECONDS` | 3600 | Query rewrite cache |
| `KB_ANSWER_CACHE_TTL_SECONDS` | 1800 | Cached RAG answers |
| `COHERE_RERANK_MODEL` | rerank-v3.5 | Cohere reranker model |

## Tech decisions

1. **pgvector halfvec(3072) + HNSW** — Native Postgres hybrid search; no external vector DB.
2. **RRF over score blending** — Rank-based fusion avoids normalizing incompatible vector/text scores.
3. **Cohere with LLM/BM25 fallback** — Premium reranking when available; graceful degradation.

## Talking points

- Retrieval is cached per org + KB version — re-ingest invalidates automatically via version bump.
- MMR prevents the LLM from seeing five nearly identical chunks about the same pain point.
- Campaign generation filters kinds: `company_profile`, `icp_profile`, `competitive_snapshot`, `document`, `campaign_asset`.
