/**
 * @file apps/web/src/lib/active-org.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
export const ACTIVE_ORG_COOKIE = "stoa-active-org";

/** Active org is stored in an HttpOnly cookie; use `/v1/orgs` for the current value. */
