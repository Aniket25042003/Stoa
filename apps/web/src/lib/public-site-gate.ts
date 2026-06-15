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
  "/see-it-in-action",
  "/pricing",
  "/faq",
]);

const PRELAUNCH_PUBLIC_API = new Set(["/api/waitlist"]);

export function isPrelaunchPublicPath(pathname: string): boolean {
  return PRELAUNCH_PUBLIC_PATHS.has(pathname);
}

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
