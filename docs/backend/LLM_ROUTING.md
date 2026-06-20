# LLM Routing

**One-liner:** Multi-provider LLM calls with task-tier model selection and automatic failover.

## Why it exists

Different tasks need different model capabilities and costs — cheap models for classification/extraction, premium for synthesis and ICP. Provider outages should not block the product; failover across Vertex, OpenAI, and Anthropic keeps the platform resilient.

## How it works

1. **Load config** — `load_config()` reads `Settings` + env overrides (`STOA_LLM_PROVIDER`, `STOA_LLM_AUTO_FAILOVER`).
2. **Task tier mapping** — `TASK_TIER_MAP` assigns tiers by task name:
   - `cheap`: classify, extract, tag
   - `standard`: summarize
   - `premium`: synthesize, icp_build, campaign_plan
3. **Model selection** — `LLMConfig.model_for()` picks fast vs pro model per provider and tier.
4. **Build invoker** — Provider-specific builders create LangChain chat clients:
   - `_vertex_invocation()` → `ChatVertexAI`
   - `_openai_invocation()` → `ChatOpenAI`
   - `_anthropic_invocation()` → `ChatAnthropic`
5. **Failover chain** — `fallback_chain` property orders providers:
   - Primary Vertex → OpenAI → Anthropic
   - Primary OpenAI → Vertex → Anthropic
   - Primary Anthropic → Vertex → OpenAI
6. **Invoke** — `_invoke_chain()` tries each provider; logs warning and continues on failure.
7. **Public API**:
   - `invoke_text(system, user, task_name=...)` — Returns `(content, provider_used)`
   - `invoke_json(system, payload, task_name=...)` — Parses JSON response, strips markdown fences

### Synthesis prompt (RAG answer)

[`services/core/src/stoa_core/rag/answer.py`](../../services/core/src/stoa_core/rag/answer.py):

- **System**: "Answer using ONLY the provided context. Cite evidence using [doc:ID] or [signal:ID]..."
- **User**: Question + up to 30 context lines formatted as `[ref] text`
- **Task**: `task_name="synthesize"` → premium tier

## Architecture diagram

```
invoke_text(system, user, task_name)
         │
         ▼
   TASK_TIER_MAP → cheap | standard | premium
         │
         ▼
   load_config() → LLMConfig
         │
         ▼
   fallback_chain: [primary, ...fallbacks]
         │
    ┌────┴────┬────────────┐
    ▼         ▼            ▼
  Vertex    OpenAI     Anthropic
  (Gemini)  (GPT)      (Claude)
         │
         ▼
   (content, provider) or (None, None)
```

## Key code callouts

- **`LLMConfig.fallback_chain`** — [`services/core/src/stoa_core/llm/router.py`](../../services/core/src/stoa_core/llm/router.py) — Determines provider order.
- **`invoke_text()`** — Used by `answer_question()`, `extract_signals()`, campaign generation.
- **`invoke_json()`** — Used by rerank fallback, ICP build, signal extraction.
- **Default models** — Vertex: `gemini-2.5-pro` / `gemini-2.5-flash`; configurable via env.

## Tech decisions

1. **LangChain provider adapters** — Unified invoke interface; swap providers without changing call sites.
2. **Task-tier routing** — Cost control: don't run premium models for classification.
3. **Env override layer** — `STOA_LLM_*` env vars override Settings for ops flexibility without redeploying config files.

## Talking points

- Failover is sequential, not parallel — first success wins.
- JSON responses strip markdown code fences automatically (`_strip_fence`).
- Timeout default: 60 seconds (`LLM_TIMEOUT_SECONDS`); temperature 0.25.
- Embeddings use a separate path (`stoa_core/ingestion/embed.py`) — not routed through this module.
