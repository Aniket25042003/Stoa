# Phase 1c — Unified Knowledge Base + Hybrid RAG

## Scope

- Single org-scoped semantic memory (`knowledge_items` + `knowledge_chunks`)
- Hybrid retrieval: pgvector `halfvec(3072)` cosine + Postgres full-text, fused via RRF
- Reranker + MMR dedup + token-budget trimming before every LLM call
- All features write to and read from the same KB

## Schema

- `knowledge_items` — source records (any `kind`: document, company_profile, icp_profile, competitive_snapshot, campaign_asset, …)
- `knowledge_chunks` — embedded chunks with `halfvec(3072)` HNSW index + `tsvector` GIN index
- RPC: `match_knowledge(org_id, embedding, query_text, kinds[], match_count, rrf_k)`

## Write path

`stoa_core.rag.ingest.ingest_knowledge(org_id, kind, title, text, …)`

Triggered by:
- Document ingestion (`kind=document`)
- Org profile update (`kind=company_profile`)
- ICP rebuild (`kind=icp_profile`)
- Competitive scan (`kind=competitive_snapshot`)
- Campaign completion (`kind=campaign_asset`)
- Content generation (`kind=content_asset`)
- Future MCP/CRM connectors (new `kind` string only)

Idempotent on `uri` + `content_hash`. Bumps Redis `kb_version` on every write.

## Read path

`stoa_core.rag.retrieve.retrieve_context(org_id, query, kinds=None)`

1. Redis query-embedding cache
2. `match_knowledge` RPC (RRF fusion)
3. Reranker cascade: Cohere → Vertex batch LLM (single call) → BM25
4. MMR dedup
5. Token-budget trim → `[{ref, text, score, kind, item_title}]`

## Config (env / Settings)

- `embed_model=gemini-embedding-001`, `embed_dimensions=3072`
- `retrieval_candidate_k=40`, `retrieval_final_k=12`, `retrieval_token_budget=2000`
- `COHERE_API_KEY` enables primary Cohere rerank; without it, Vertex batch LLM then BM25 apply automatically
- `kb_cache_ttl_seconds=3600`

## Backfill

Celery task `knowledge.reembed_org(org_id)` migrates existing documents, profiles, ICP, and competitor snapshots into the unified KB.

## Definition of Done

- [x] RLS on knowledge tables
- [x] Hybrid RPC with org + kind filter
- [x] All LLM paths use `retrieve_context`
- [x] Derived artifacts written back to KB
- [x] Tests: chunking, ingest idempotency, retrieval budgeting, reranker
- [x] Redis TTL on cache keys
