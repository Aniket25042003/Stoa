# ADR-006: Tiered agent routing and bounded tool execution

## Status

Accepted

## Context

The unified GTM agent used a binary route (`rag_only` vs `tools`) with an org-blind classifier.
Simple questions that matched fresh `precomputed_insights` (e.g. top converting customers)
still entered a LangChain `AgentExecutor` loop, causing 4+ LLM round trips and ~60–90s latency.

Vertex `ChatVertexAI` is deprecated in LangChain 3.2+; content-block responses required
extra normalization.

## Decision

1. **Four execution tiers** resolved by `resolve_agent_route(org_id, question, history)`:
   - `precomputed_enriched` — matched fresh insight + CRM stats + optional light retrieval → 1 synthesis LLM call
   - `rag_only` — hybrid RAG + optional structured CRM prefix → 1–2 LLM calls
   - `tools_bounded` — plan (1 LLM) + parallel tools (≤3) + synthesize (1 LLM)
   - `tools_react` — fallback `AgentExecutor` with `max_iterations=3`

2. **Org-aware precomputed matching** — Jaccard similarity against `COMMON_QUESTIONS` templates
   and insight titles; embedding cosine for borderline scores; stale insights downgrade to `rag_only`.

3. **Bounded agent** replaces reactive loop as the default tools path (`bounded_agent.py`).

4. **LLM client migration** — `langchain-google-genai` `ChatGoogleGenerativeAI` via
   `build_chat_model()` (Vertex ADC default, `GOOGLE_API_KEY` fallback); legacy `ChatVertexAI`
   when `llm_vertex_backend=vertexai_legacy`.

5. **Structured logging** — `agent_turn` log line includes `route`, `reason`, `insight_key`,
   `llm_calls_est`, `duration_ms`.

## Consequences

- Demo ICP questions should complete in one synthesis call when precomputed insights exist.
- Cross-feature questions retain tool access with a predictable 2-LLM budget on the bounded path.
- `classify_agent_route()` remains for legacy compatibility; new code uses `resolve_agent_route()`.
- Keyword heuristics for tools are tighter (word boundaries) to reduce false positives.

## Alternatives considered

- **Always use AgentExecutor** — rejected (latency, redundant retrieval).
- **Return precomputed answers without synthesis** — rejected (quality; paraphrased questions need adaptation).
- **Faster models for synthesis** — deferred until quality metrics show regression.
