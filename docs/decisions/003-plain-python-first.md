# ADR-003: Plain Python orchestration first

**Status:** Accepted

## Context

LangGraph provides checkpointing but adds opacity for memory and debugging. Phase 1 is mostly deterministic pipelines + RAG.

## Decision

Phases 0–1 use plain typed Python in `stoa_core` + Celery. Introduce LangGraph in Phase 3 for campaign generate→critic→revise loops only.

## Consequences

- Explicit memory reads/writes to Postgres/Redis/pgvector
- Easier testing and debugging
- LangGraph adopted only where resumability earns its cost
