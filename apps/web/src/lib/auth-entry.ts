/**
 * Auth entry routing:
 * - `next dev` (NODE_ENV=development): /login
 * - Loopback hosts (localhost, 127.0.0.1): /login — for local prod-build smoke tests
 * - Production deployments: /waitlist
 *
 * Override with NEXT_PUBLIC_AUTH_ENTRY=login|waitlist
 */
export type AuthEntryPath = "/login" | "/waitlist";

type AuthEntryOptions = {
  hostname?: string;
};

function resolveHostname(hostname?: string): string | undefined {
  if (hostname) return hostname;
  if (typeof window !== "undefined") return window.location.hostname;
  return undefined;
}

function isLoopbackHost(hostname: string | undefined): boolean {
  if (!hostname) return false;
  const host = hostname.toLowerCase();
  return host === "localhost" || host === "127.0.0.1" || host === "[::1]";
}

export function getAuthEntryPath(options?: AuthEntryOptions): AuthEntryPath {
  const override = process.env.NEXT_PUBLIC_AUTH_ENTRY;
  if (override === "login") return "/login";
  if (override === "waitlist") return "/waitlist";

  const hostname = resolveHostname(options?.hostname);
  if (process.env.NODE_ENV === "development" || isLoopbackHost(hostname)) {
    return "/login";
  }
  return "/waitlist";
}

export function isLoginEnabled(hostname?: string): boolean {
  return getAuthEntryPath({ hostname }) === "/login";
}
