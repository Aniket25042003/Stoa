/**
 * @file apps/web/src/lib/auth-workflow.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
export type SessionState = {
  user?: {
    id: string;
    email?: string | null;
    auth_provider?: string | null;
    email_verified?: boolean;
  };
  user_profile?: Record<string, unknown> | null;
  membership?: {
    id: string;
    org_id: string;
    role?: string;
    role_name?: string | null;
    role_key?: string | null;
  } | null;
  memberships?: Array<{
    id: string;
    org_id: string;
    role?: string;
    role_name?: string | null;
    role_key?: string | null;
    org?: Record<string, unknown> | null;
  }>;
  org?: Record<string, unknown> | null;
  permissions?: string[];
  needs_email_verification?: boolean;
  needs_onboarding?: boolean;
};

/**
 * Handles safe next path behavior for this part of the Stoa application.
 *
 * @param raw - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
export function safeNextPath(raw: string | null | undefined): string {
  if (!raw) return "/dashboard";
  if (!raw.startsWith("/") || raw.startsWith("//") || raw.includes("\\")) {
    return "/dashboard";
  }
  try {
    const decoded = decodeURIComponent(raw);
    if (decoded.startsWith("//") || decoded.includes("://")) {
      return "/dashboard";
    }
  } catch {
    return "/dashboard";
  }
  if (!/^\/[A-Za-z0-9/_.?=&-]*$/.test(raw)) {
    return "/dashboard";
  }
  return raw;
}

/**
 * Handles route for session state behavior for this part of the Stoa application.
 *
 * @param state - Input value used to render UI or execute the workflow.
 * @param next - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function routeForSessionState(state: SessionState, next: string = "/dashboard") {
  const safeNext = safeNextPath(next);
  if (state.needs_email_verification) {
    return `/verify-email?next=${encodeURIComponent(safeNext)}`;
  }
  if (safeNext.startsWith("/invite/")) {
    return safeNext;
  }
  if (state.needs_onboarding && safeNext !== "/onboarding") {
    return "/onboarding";
  }
  return safeNext;
}

/**
 * Handles can read behavior for this part of the Stoa application.
 *
 * @param permissions - Input value used to render UI or execute the workflow.
 * @param perm - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
export function canRead(permissions: string[] | undefined, perm: string): boolean {
  if (!permissions) return true;
  return permissions.includes(perm);
}

/** Nav-only: hide items until permissions are loaded to avoid flash of unauthorized links. */
export function canReadNav(
  permissions: string[] | null | undefined,
  perm: string,
  permissionsLoaded: boolean
): boolean {
  if (!permissionsLoaded) return false;
  if (permissions === null) return true;
  if (!permissions) return false;
  return permissions.includes(perm);
}
