# Research Tool Orchestration Issue Plan

## Summary

The current implementation correctly replaced the previous stdio MCP dependency with a direct in-process research tool registry, but the multi-agent orchestration around those tools is still behaving like an expensive LLM review loop. The research integrations can return useful results quickly when called directly, yet end-to-end runs stall because planning, subagent review, and parent approval repeatedly call the large model and do not mutate failed tool calls between retry attempts.

Test run used:

- User: `test@gmail.com`
- Run ID: `a8f1a1ad-61b2-43de-b9ae-b05d43dffdc7`
- API: `http://localhost:8000`
- Web: `http://localhost:3000`
- Environment: external research enabled, Vertex primary, `gemini-2.5-pro`, Tavily/Jina/SerpAPI configured

## Current Architecture Observed

- UI creates runs through FastAPI and requires user approval before Celery starts the agent pipeline.
- FastAPI creates the master plan synchronously in `POST /v1/runs`.
- Celery executes the LangGraph graph: orchestrator -> research -> reasoning -> validation -> writer.
- Research tools are now exposed through the direct registry in `gtm_agents.mcp_client`, despite the docs and some comments still referring to MCP.
- Direct tools available at runtime:
  - `crawl_web`
  - `crawl_search_results`
  - `web_research`
  - `competitor_research`
  - `full_research_suite`
- The old MCP server still exists in `services/mcp/research_server.py`, but the active agent path uses direct function calls.

## Evidence From Testing

1. Existing test suite:
   - Command: `cd services/api && pytest -q tests/test_graph_smoke.py tests/test_llm_provider.py tests/test_crawler_tool.py`
   - Result: `13 passed, 1 skipped`
   - Duration: `101.34s`
   - Concern: this is too slow for a smoke suite because graph planning still initializes/invokes live provider paths.

2. Auth/API path:
   - Password auth for the provided test user succeeded.
   - `POST /v1/runs` timed out after a 60-second client timeout.
   - The run eventually appeared in Supabase as `awaiting_plan_approval`.
   - Root cause: `create_run` calls `create_master_plan_for_user` synchronously before inserting and returning the run.

3. Direct tool diagnostic:
   - `list_research_tools()` returned all five direct tools.
   - `plan_research_calls(...)` took `38.61s`.
   - A direct `web_research` call returned `3` items in `3.24s` with no warnings.
   - Interpretation: the research providers are not the primary latency source; the LLM planning/review layer is.

4. End-to-end approved run:
   - After approval, the run stayed `running` for at least 6 minutes.
   - No persisted sources and no report were available during that window.
   - Redis memory showed progress inside research subagents, but the API event stream only showed four coarse events and then appeared stuck:
     - `Starting GTM pipeline`
     - `Planning research objectives`
     - `Reading the approved master plan`
     - `Research layer is choosing sources and delegating research agents`

5. Failed retry behavior in Redis memory:
   - A `crawl_search_results_subagent` received parent feedback that the query was too specific and should be broadened.
   - Iteration 2 executed the same selected tool call again instead of applying the revised query.
   - A `competitor_research_subagent` received feedback to split `Clay.com` and `Regie.ai` into separate searches.
   - Iteration 2 again reused the same combined query.
   - This confirms retries are review-only; they do not update `selected_call.arguments`.

## Root Causes

### 1. Synchronous master-plan generation blocks run creation

Location: `services/api/app/routers/runs.py`

`create_run` calls `create_master_plan_for_user(payload)` before inserting the run and returning the response. With `gemini-2.5-pro`, this can exceed normal HTTP request budgets.

Impact:

- Users can see request timeouts even though the run is later created.
- The frontend may show an error while the database contains a valid awaiting-approval run.
- Duplicate run creation is likely if the user retries.

### 2. Too many large-model calls in the critical path

Location: `services/agents/src/gtm_agents/autonomy.py`

The pipeline uses LLM calls for:

- master plan creation
- research parent plan
- research call planning
- every subagent plan
- every subagent self-review
- every parent approval
- revision instruction generation
- reasoning subagent synthesis/review
- writer planning/review

With `gemini-2.5-pro` as the only active provider, simple planning and review steps dominate runtime.

### 3. Revision feedback does not change tool calls

Location: `run_planned_agent` and the research subagent closure inside `autonomous_research`

`run_planned_agent` can append `fix_*` steps after a rejection, but the `work_fn` receives the same original `selected_call` closure on every iteration. Parent feedback can say "broaden query" or "split competitors," but there is no mechanism to produce and execute a revised tool call.

Impact:

- Failed searches repeat unchanged.
- The system spends expensive LLM calls reviewing the same failure.
- Parent/subagent approval loops create the appearance of autonomy without operational adaptation.

### 4. Research source persistence happens too late

Location: `services/api/app/tasks/gtm.py`

Research sources are persisted only after the entire graph completes. During long research runs, the UI shows zero sources even when subagents have already produced useful items.

Impact:

- The system looks stalled.
- Partial successful research is lost if a later phase fails.
- Debugging requires manually inspecting Redis memory.

### 5. Tool execution is sequential and under-instrumented

Location: `autonomous_research` and `mcp_client.call_research_tools`

Selected research calls are executed one subagent at a time. Long `crawl_search_results` or review steps block all other useful calls. Tool-level start/end events are not emitted to Redis/Supabase.

Impact:

- Slow or bad first calls delay useful later calls.
- The UI cannot show which tool is currently running.
- There is no duration/error telemetry per tool call unless LangSmith is inspected.

### 6. Documentation still describes MCP as the active research path

Locations:

- `README.md`
- `AGENT.md`
- `services/mcp/README.md`

The active implementation uses direct tool calls, but docs still say the research supervisor talks to MCP over stdio. This makes debugging and onboarding misleading.

## Resolution Plan

### Phase 1: Make run creation reliable

1. Change `POST /v1/runs` to insert the run immediately with status `planning`.
2. Enqueue a lightweight Celery task, for example `gtm.create_master_plan`, to generate the master plan.
3. When plan generation completes, update status to `awaiting_plan_approval`.
4. Add an idempotency key or request fingerprint so frontend retries do not create duplicate runs.
5. Update the frontend to show a `planning` state before plan approval.

Acceptance criteria:

- `POST /v1/runs` returns in under 2 seconds.
- Slow LLM plan generation no longer causes client-visible request timeouts.
- A failed plan-generation task marks the run `failed` with a clear error.

### Phase 2: Split model selection by task complexity

1. Add model routing in `gtm_agents.llm`, not scattered through agent code.
2. Define task tiers:
   - `cheap`: plan normalization, JSON repair, self-review, parent approval, tool-call revision.
   - `standard`: research call selection and short synthesis.
   - `premium`: final reasoning synthesis and report writing.
3. Use `gemini-2.5-flash` for cheap/standard steps when Vertex is active.
4. Keep `gemini-2.5-pro` for premium reasoning and final report generation.
5. Add env vars:
   - `GTM_VERTEX_MODEL_FAST=gemini-2.5-flash`
   - `GTM_VERTEX_MODEL_PRO=gemini-2.5-pro`
   - `GTM_LLM_DEFAULT_TIER=fast`
6. Add span metadata with `task_tier`, `model`, and duration.

Acceptance criteria:

- Existing smoke tests finish in under 20 seconds without live external calls.
- A full live research run spends large-model calls only on high-value synthesis/writing.

### Phase 3: Implement real adaptive retries for research calls

1. Add a structured retry output contract:
   ```json
   {
     "action": "retry_with_modified_call|split_calls|skip_tool|accept_with_warnings",
     "revised_calls": []
   }
   ```
2. After self-review or parent rejection, generate revised calls from the failure context.
3. Replace the immutable `selected_call` closure with mutable iteration state.
4. For zero-result search failures:
   - broaden query
   - remove excessive quoted phrases
   - lower specificity
   - use `web_research` before `crawl_search_results`
5. For multi-entity competitor failures:
   - split competitors into separate `competitor_research` calls
   - merge and dedupe results afterward
6. Cap retries per original call and enforce a total research budget.

Acceptance criteria:

- If a query returns zero items, iteration 2 executes a different query.
- If a competitor query combines multiple companies and misses one, iteration 2 splits it.
- Redis memory records both the original and revised call arguments.

### Phase 4: Improve research planner guardrails

1. Validate LLM-selected calls before execution.
2. Reject or rewrite risky calls:
   - `crawl_search_results` with very narrow exact-match forum queries.
   - combined competitor queries with multiple named companies.
   - excessive `max_results`, `max_pages_per_result`, or `max_depth`.
3. Prefer this default order:
   - `web_research` for broad discovery.
   - `competitor_research` split by competitor/entity.
   - `crawl_search_results` only after discovery shows URLs worth deepening.
   - `crawl_web` only for known URLs.
4. Add deterministic fallback call expansion when planner output is weak.

Acceptance criteria:

- The planner cannot execute a query pattern known to return zero results without rewrite.
- Multi-competitor inputs produce one call per competitor.
- Crawl tools are used selectively after search has useful seed URLs.

### Phase 5: Persist partial research and stream tool events

1. Emit events at tool start, tool success, tool warning, tool failure, and retry.
2. Persist research sources as soon as each tool returns items.
3. Store failed tool attempts in `agent_artifacts` with arguments, warnings, duration, and approval outcome.
4. Update the run detail UI to show:
   - active tool name
   - query
   - duration
   - source count per tool
   - retry reason

Acceptance criteria:

- During a long run, sources appear before the graph completes.
- The user can see exactly which tool/query is running.
- A failed later phase does not erase earlier successful research evidence.

### Phase 6: Parallelize independent research calls

1. Execute independent research calls concurrently with a bounded worker pool.
2. Keep crawl concurrency lower than web/competitor search concurrency.
3. Apply a per-tool timeout:
   - `web_research`: 20-30 seconds
   - `competitor_research`: 20-30 seconds
   - `crawl_search_results`: 60-90 seconds
   - `crawl_web`: 90-120 seconds
4. Use partial results when one tool fails or times out.

Acceptance criteria:

- A bad first crawl cannot block all other research calls.
- Research phase returns useful partial evidence within the configured budget.

### Phase 7: Tighten tests

1. Add unit tests for direct tool registry names and schemas.
2. Add planner validation tests:
   - multi-competitor query splitting
   - zero-result query rewrite
   - crawl budget caps
3. Add a fake research tool that returns zero results on the first call and success on the revised call.
4. Add an API test proving `POST /v1/runs` returns quickly and plan generation happens asynchronously.
5. Keep live crawler tests opt-in.

Acceptance criteria:

- CI does not depend on Vertex/OpenAI credentials for core smoke tests.
- Adaptive retry behavior is covered without live network calls.

### Phase 8: Update docs

1. Update `README.md`, `AGENT.md`, and `services/mcp/README.md`.
2. State that the production path uses direct in-process tools.
3. Keep MCP documented as optional compatibility only.
4. Document the model-tier policy and recommended defaults:
   - `gemini-2.5-flash` for planning/review/tool-call repair.
   - `gemini-2.5-pro` for deep synthesis/final report.

## Suggested Priority

1. First fix: asynchronous master-plan generation.
2. Second fix: adaptive research retries that actually mutate tool calls.
3. Third fix: model-tier routing to reduce latency/cost.
4. Fourth fix: partial source persistence and tool-level events.
5. Fifth fix: bounded parallel research execution.

These changes address the core failure mode directly: tools are available and functional, but the orchestration currently spends too much time reviewing and retrying unchanged tool calls.
