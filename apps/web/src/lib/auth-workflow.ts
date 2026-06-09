export type SessionState = {
  user?: {
    id: string;
    email?: string | null;
    auth_provider?: string | null;
    email_verified?: boolean;
  };
  user_profile?: Record<string, unknown> | null;
  membership?: { id: string; org_id: string; role: string } | null;
  org?: Record<string, unknown> | null;
  needs_email_verification?: boolean;
  needs_onboarding?: boolean;
};

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
  if (!/^\/[A-Za-z0-9/_-]*$/.test(raw)) {
    return "/dashboard";
  }
  return raw;
}

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
