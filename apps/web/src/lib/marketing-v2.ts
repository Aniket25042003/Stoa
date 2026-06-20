/**
 * @file apps/web/src/lib/marketing-v2.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
/** Routes that use the cream / indigo marketing v2 chrome (navbar, footer, page tokens). */
import { PRELAUNCH_PUBLIC_PATHS } from "@/lib/public-site-gate";

const MARKETING_V2_EXACT = PRELAUNCH_PUBLIC_PATHS;

/**
 * Handles is marketing v2 page behavior for this part of the Stoa application.
 *
 * @param pathname - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
export function isMarketingV2Page(pathname: string | null): boolean {
  if (!pathname) return false;
  return MARKETING_V2_EXACT.has(pathname);
}
