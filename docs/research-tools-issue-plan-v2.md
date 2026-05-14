# Research Tool Orchestration Issue Plan V2

## What Was Fixed In This Pass

1. **Run creation no longer blocks on LLM planning**
   - `POST /v1/runs` now creates a run immediately with status `planning`.
   - A Celery task `gtm.create_master_plan` generates the master plan asynchronously.
   - `POST /v1/runs/{id}/plan/revise` now reuses the async planning path.
   - Supabase migration `20260514000000_add_planning_run_status.sql` was applied to the remote database.

2. **Cheap/standard/premium model tiers were added**
   - Planning and review calls now route through the cheap/standard tier.
   - Vertex defaults:
     - cheap/standard: `gemini-2.5-flash`
     - premium: `gemini-2.5-pro`
   - Final reasoning/report writing remains on the premium tier.

3. **Research retries now mutate tool calls**
   - Zero-result `crawl_search_results` calls can retry as broader `web_research`.
   - Combined competitor searches split into focused `competitor_research` calls per competitor.
   - Retry changes are recorded in Redis memory as `tool_call_revised`.

4. **Planner guardrails were added**
   - Narrow boolean/site-filter crawl queries are rewritten to broader web research.
   - Crawl result/page budgets are capped before execution.
   - Multi-competitor planner calls are split before execution.

5. **Partial research persistence and tool events were added**
   - Research sources are persisted as soon as each tool returns.
   - Tool start/finish/persist events are written to the event stream and `run_events`.
   - The live run showed sources appearing while the pipeline was still running.

6. **Playwright missing-browser fallback was improved**
   - `run_crawl` now preflights Chromium availability and falls back to HTTP extraction immediately when browsers are missing.
   - HTTP fallback page and timeout caps were added.

7. **Research budget/good-enough gates were added after the first V2 diagnostic**
   - Research now tracks elapsed seconds and tool-call count.
   - Research auto-approves when `GTM_RESEARCH_MIN_SOURCES_FOR_APPROVAL` is met and there are no fatal warnings.
   - The second live run confirmed research progressed to reasoning on attempt 1 with 15 sources.

## Verification Results

### Automated Tests

- `cd services/api && pytest -q`
- Result: `21 passed, 1 skipped`
- Runtime: about `2s`

### Web Build

- `pnpm --filter web build`
- Result: passed.
- One React hook dependency warning was fixed afterward.

### Live Workflow Test

Run ID: `616fb446-5141-4a0b-b4e9-0a7854df2e76`

Observed:

- `POST /v1/runs` returned in `0.36s` with status `planning`.
- Master plan generation completed in about `37s`.
- Plan approval successfully queued the GTM pipeline.
- Partial source persistence worked:
  - 7 sources appeared during execution.
  - then 12
  - then 21
  - then 33
  - then 38
- Adaptive retry worked:
  - competitor research split into separate Clay and Perplexity calls.
  - tool start/finish/persist events appeared in `run_events`.

The run did not complete within the verification window and was manually marked failed as a diagnostic run.

Second run after adding research gates:

- Run ID: `ba360f51-b3dd-47ba-bb8c-c6a3c954eda1`
- `POST /v1/runs` returned in `0.78s`.
- Master plan generation completed in about `26s`.
- Research collected and persisted `15` sources.
- Research was approved on attempt 1.
- The run then stalled in the reasoning layer and was marked failed as a diagnostic run after the reasoning timeout fix was added.

## Remaining Issues

### 1. Reasoning/writing can still exceed a practical runtime budget

Research now exits once enough evidence exists, but the second live run stalled in the reasoning layer after research approval.

Root cause:

- Section-level reasoning was still too dependent on live LLM latency.
- There is no hard reasoning-layer or writing-layer wall-clock budget.
- Parent/subagent review loops can still wait on slow provider calls.

Fix plan:

1. Add `GTM_REASONING_MAX_SECONDS`, default `180`.
2. Add `GTM_WRITING_MAX_SECONDS`, default `180`.
3. Use deterministic fallback section outputs when section synthesis exceeds timeout.
4. Emit reasoning subagent start/finish events like research tools do.
5. Add explicit provider request timeout verification tests.
6. Consider using `gemini-2.5-flash` for all reasoning subagents and reserving `gemini-2.5-pro` only for final report polishing.

Acceptance criteria:

- Reasoning phase exits within the configured budget.
- A run with 12+ sources produces either a final report or a deterministic fallback report within 10 minutes.

### 2. Crawl tools still need a production execution policy

The local environment did not have Playwright Chromium installed. The new preflight avoids repeated browser launch failures, but the workflow still needs a clear policy for when browser crawl is allowed.

Fix plan:

1. Add `GTM_ENABLE_BROWSER_CRAWL=false` as the local default.
2. Only expose `crawl_web` and `crawl_search_results` to the planner when:
   - `GTM_ENABLE_BROWSER_CRAWL=true`
   - Chromium is installed
3. Otherwise expose a lightweight tool description:
   - `crawl_search_results_light`
   - implemented as search + capped HTTP extraction
4. In Railway/Nixpacks, ensure `playwright install chromium --with-deps` runs for both API and worker images.

Acceptance criteria:

- Local runs do not attempt browser crawling unless browsers are installed.
- Production workers fail startup health checks if browser crawl is enabled but Chromium is missing.

### 3. Research calls are still sequential

The direct tool registry works, but independent calls execute serially inside `autonomous_research`.

Fix plan:

1. Add a bounded thread pool for I/O-bound direct tool calls.
2. Run independent `web_research` and `competitor_research` calls concurrently.
3. Keep browser crawl concurrency separate and low.
4. Preserve event ordering with per-call IDs.

Acceptance criteria:

- A research plan with 4 independent web/competitor calls completes in roughly the duration of the slowest call, not the sum of all calls.

### 4. Master-plan generation is async but still slow

Plan generation no longer blocks the browser, but the live run still took about `37s` to draft the plan.

Fix plan:

1. Make master-plan generation deterministic by default.
2. Use LLM only to refine user-facing wording when enabled.
3. Keep the plan to 5-7 canonical steps.
4. Add `GTM_MASTER_PLAN_MODE=deterministic|llm`, default `deterministic` locally.

Acceptance criteria:

- Master plan is ready in under 5 seconds in deterministic mode.

### 5. Local Celery prefork was unreliable on macOS

The local prefork worker exited during testing. Running with `--pool=solo` was stable.

Fix plan:

1. Update local runbook to recommend:
   - `celery -A app.celery_app worker -l info --pool=solo --concurrency=1`
2. Keep prefork for Linux/Railway.
3. Add a worker health check command to the runbook.

Acceptance criteria:

- Local worker stays online long enough to complete a full run.

## Recommended Next Implementation Order

1. Add reasoning/writing wall-clock budget gates and fallback outputs.
2. Hide browser crawl tools unless browser crawl is enabled and Chromium is installed.
3. Make master-plan generation deterministic by default.
4. Add bounded parallel execution for independent search tools.
5. Update runbook with local Celery and Playwright instructions.
