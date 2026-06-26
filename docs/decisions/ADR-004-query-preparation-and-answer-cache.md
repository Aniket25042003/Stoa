# ADR-004: Query preparation and answer caching

## Status

Accepted

## Context

Short or context-dependent user questions retrieve poorly when embedded verbatim. The agent path also paid full premium tool-calling cost for simple factual questions. Repeated similar questions re-ran retrieval and synthesis with no cache beyond embeddings/results.

## Decision

1. **Query preparation** — Before retrieval on agent turns, run a cheap LLM rewrite (`query_rewrite` tier) when heuristics detect short or deictic queries. Emit 1–3 `search_queries`, retrieve each, merge and dedupe.
2. **Route classification** — Cheap classifier (`needs_tools` tier) routes simple questions to RAG-only synthesis; multi-feature questions use the tool-calling agent (premium).
3. **Expanded Redis caches** — KB-version-keyed caches for query rewrites and final RAG answers. Retrieval cache keys optionally include `conversation_id` for thread-scoped memory.
4. **Retrieval hardening** — Enforce `RETRIEVAL_MIN_SIMILARITY` on vector-only hits; fail loudly on unavailable embeddings; filter `conversation_memory` by thread.
5. **Ask idempotency** — `Idempotency-Key` header on `/v1/conversations/ask`; Celery worker skips duplicate assistant inserts when a reply already exists for the user message.

## Consequences

- Better recall for terse prompts without always paying rewrite cost on long questions.
- Lower latency/cost for RAG-only turns; premium model reserved for cross-feature tool use.
- Stale answers possible until KB version bump — acceptable for read-heavy Q&A; tool routes still read live DB via tools.
- No schema migration required for idempotency (Redis + message ordering checks).
