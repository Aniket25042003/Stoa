# ADR-002: Defer Temporal

**Status:** Accepted

## Context

Competitive monitoring needs scheduled jobs. Temporal adds operational complexity.

## Decision

Use Celery + Redis for Phases 0–2. Re-evaluate Temporal at Phase 2 for continuous monitoring if Celery beat proves insufficient.

## Consequences

- Simpler initial deployment
- May need migration path for durable scheduled workflows later
