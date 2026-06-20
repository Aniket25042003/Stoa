/**
 * @file apps/web/src/lib/auth-entry.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
/**
 * Auth entry routing:
 * - `next dev` (NODE_ENV=development): /login
 * - Loopback hosts (localhost, 127.0.0.1): /login — for local prod-build smoke tests
 * - Production deployments: /waitlist
 *
 * Override with NEXT_PUBLIC_AUTH_ENTRY=login|waitlist
 */
import { isLoopbackHost, resolveHostname } from "@/lib/host";

export type AuthEntryPath = "/login" | "/waitlist";

type AuthEntryOptions = {
  hostname?: string;
};

/**
 * Handles get auth entry path behavior for this part of the Stoa application.
 *
 * @param options - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
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

/**
 * Handles is login enabled behavior for this part of the Stoa application.
 *
 * @param hostname - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
export function isLoginEnabled(hostname?: string): boolean {
  return getAuthEntryPath({ hostname }) === "/login";
}

export type MarketingCta = {
  href: AuthEntryPath;
  navLabel: string;
  buttonLabel: string;
  heroLabel: string;
  footerDescription: string;
  bandTitle: string;
  bandDescription: string;
};

/** Primary marketing CTA — login in dev/loopback, waitlist in pre-launch production. */
export function getMarketingCta(options?: AuthEntryOptions): MarketingCta {
  if (isLoginEnabled(options?.hostname)) {
    return {
      href: "/login",
      navLabel: "Sign in",
      buttonLabel: "Sign in",
      heroLabel: "Sign in",
      footerDescription: "Sign in to access your marketing intelligence workspace.",
      bandTitle: "Open the app",
      bandDescription: "Sign in with your credentials to use the full product locally.",
    };
  }
  return {
    href: "/waitlist",
    navLabel: "Request access",
    buttonLabel: "Join the waitlist",
    heroLabel: "Request early access",
    footerDescription: "Join the waitlist for early access to precomputed marketing intelligence.",
    bandTitle: "Get on the list",
    bandDescription: "Join the waitlist while we roll out billing and team workspaces.",
  };
}
