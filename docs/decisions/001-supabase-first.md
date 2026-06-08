# ADR-001: Supabase-first foundation

**Status:** Accepted

## Context

Need Postgres, pgvector, auth (Google), storage, and RLS with minimal ops.

## Decision

Use Supabase for Postgres + pgvector + Auth + Storage + RLS. Do not self-host.

## Consequences

- Google sign-in stays trivial
- RLS enforced at DB layer for defense in depth
- Service role on API bypasses RLS — must enforce org_id in application code
