/**
 * Auth entry routing:
 * - Local dev (`next dev`): /login (Google sign-in)
 * - Production builds: /waitlist
 *
 * Override with NEXT_PUBLIC_AUTH_ENTRY=login|waitlist
 */
export type AuthEntryPath = "/login" | "/waitlist";

export function getAuthEntryPath(): AuthEntryPath {
  const override = process.env.NEXT_PUBLIC_AUTH_ENTRY;
  if (override === "login") return "/login";
  if (override === "waitlist") return "/waitlist";
  return process.env.NODE_ENV === "development" ? "/login" : "/waitlist";
}

export function isLoginEnabled(): boolean {
  return getAuthEntryPath() === "/login";
}
