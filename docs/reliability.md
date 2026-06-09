# Reliability

## Jobs

- Celery tasks: `bind=True`, `max_retries`, `task_acks_late`
- Idempotent ingestion keyed by `job_id`
- Failed jobs persist `error` on `ingestion_jobs` / `campaigns`

## SSE

- Redis Streams with `MAXLEN ~10000` + 72h TTL
- Heartbeats when no messages
- Client uses `fetch` + `ReadableStream` (not EventSource) for Bearer auth

## LLM

- Provider chain with auto-failover (Vertex → OpenAI → Anthropic)
- Task-tier routing: cheap for extract, premium for synthesis
- Graceful degradation when no provider available

## Observability

- Structured logging with request IDs
- Optional LangSmith tracing (`LANGSMITH_TRACING`)

## CI

- `ruff` lint on `services/`
- `pytest` on `services/core` and `services/api`
- `pnpm lint:web` on frontend
