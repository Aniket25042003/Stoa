/**
 * @file apps/web/src/lib/public-site-gate.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
/**
 * Pre-launch public site: production exposes only marketing + waitlist until the app ships.
 *
 * - Default: gated on Vercel production (and non-loopback prod builds).
 * - Open the full app: set NEXT_PUBLIC_APP_ENABLED=true on Vercel + redeploy.
 * - Force gate everywhere (e.g. staging): NEXT_PUBLIC_PRELAUNCH_MODE=true
 */

import { isLoopbackHost, resolveHostname } from "@/lib/host";

/** Pages reachable before the product is publicly available. */
export const PRELAUNCH_PUBLIC_PATHS = new Set([
  "/",
  "/waitlist",
]);

/** Legacy marketing routes merged into the single-page landing. */
export const PRELAUNCH_LEGACY_REDIRECTS: Record<string, string> = {
  "/see-it-in-action": "/#how-it-works",
  "/pricing": "/#pricing",
  "/faq": "/#faq",
  "/how-it-works": "/#how-it-works",
};

/**
 * @param pathname - Request path without query string.
 * @returns Anchor redirect target on `/`, or null.
 */
export function getPrelaunchLegacyRedirect(pathname: string): string | null {
  return PRELAUNCH_LEGACY_REDIRECTS[pathname] ?? null;
}

const PRELAUNCH_PUBLIC_API = new Set(["/api/waitlist"]);

/**
 * Handles is prelaunch public path behavior for this part of the Stoa application.
 *
 * @param pathname - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
export function isPrelaunchPublicPath(pathname: string): boolean {
  return PRELAUNCH_PUBLIC_PATHS.has(pathname);
}

/**
 * Handles is prelaunch public api behavior for this part of the Stoa application.
 *
 * @param pathname - Input value used to render UI or execute the workflow.
 * @param method - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
export function isPrelaunchPublicApi(pathname: string, method: string): boolean {
  if (!PRELAUNCH_PUBLIC_API.has(pathname)) return false;
  const verb = method.toUpperCase();
  return verb === "POST" || verb === "OPTIONS" || verb === "HEAD";
}

/**
 * When true, only {@link PRELAUNCH_PUBLIC_PATHS} and the waitlist API are exposed.
 */
export function isPublicSiteOnlyMode(hostname?: string): boolean {
  const appEnabled = process.env.NEXT_PUBLIC_APP_ENABLED;
  if (appEnabled === "true") return false;
  if (appEnabled === "false") return true;

  const prelaunch = process.env.NEXT_PUBLIC_PRELAUNCH_MODE;
  if (prelaunch === "true") return true;
  if (prelaunch === "false") return false;

  const host = resolveHostname(hostname);
  if (process.env.NODE_ENV === "development" || isLoopbackHost(host)) {
    return false;
  }

  // Vercel preview deployments stay fully available for QA unless forced above.
  if (process.env.VERCEL_ENV === "preview") return false;

  return true;
}
