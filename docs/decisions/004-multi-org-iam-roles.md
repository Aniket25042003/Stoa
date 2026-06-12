# ADR-004: Multi-Org Tenancy + IAM-Style Roles

## Status

Accepted — 2026-06-12

## Context

Stoa originally enforced one organization per user (`memberships.user_id` unique) with four hardcoded roles. This caused:

1. Invite acceptance deleting placeholder orgs (data-loss edge cases)
2. No way for a user to be owner of Company A and analyst at Company B
3. Rigid RBAC without custom roles
4. Onboarding inside the product shell with client-side gating only

## Decision

### Multi-org tenancy

- Drop `unique(user_id)` on `memberships`; keep `unique(org_id, user_id)`.
- Active org resolved per request: `X-Org-Id` → `last_active_org_id` → sole membership → `409 org_selection_required`.
- Disable `handle_new_user_org` trigger; orgs created at `POST /v1/onboarding/complete`.

### IAM-style roles

- New `org_roles` table with `permissions text[]`.
- Four immutable system roles seeded per org; owners create custom roles from a `resource:action` catalog in `stoa_core.security.permissions`.
- `roles:manage` delegatable with permission boundary (non-owners cannot grant beyond their own set).
- Owner-reserved: `org:delete`, `org:transfer_ownership`.

### RLS

- Replace `current_org_id()` / `has_min_role` with `is_org_member(org_id)` and `has_permission_in_org(org_id, perm)`.
- Table-level coarse access at RLS; API enforces fine-grained permissions via `OrgScope`.

### Dedicated onboarding

- `(onboarding)` route group with minimal shell; `(app)/layout.tsx` server-redirects incomplete users.
- `GET /v1/onboarding/context` + `POST /v1/onboarding/complete` (atomic write).
- Product routers use `require_onboarded_scope` → `403 onboarding_required`.

### Additive invites

- `accept_invite` inserts/syncs membership only; no org deletion.
- `profile_hints` on invites prefill invitee wizard.

## Consequences

- Org switcher + `X-Org-Id` propagation required in web BFF and server fetches.
- All API routers migrated from `get_user_membership` to `get_org_scope` + `require_permission`.
- RLS integration tests must seed `org_roles` for fixture orgs.
- Documentation and AGENTS.md tenancy section updated.

## Alternatives considered

- **Keep single-org, allow org transfer on invite** — rejected; loses multi-org product requirement.
- **Replace RBAC with ABAC only** — rejected; IAM-style roles are simpler for marketing teams.
- **Client-only onboarding gate** — rejected; users could reach product tabs before org exists in DB/RAG.
