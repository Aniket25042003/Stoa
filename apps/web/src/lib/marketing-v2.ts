/** Routes that use the cream / indigo marketing v2 chrome (navbar, footer, page tokens). */
import { PRELAUNCH_PUBLIC_PATHS } from "@/lib/public-site-gate";

const MARKETING_V2_EXACT = PRELAUNCH_PUBLIC_PATHS;

export function isMarketingV2Page(pathname: string | null): boolean {
  if (!pathname) return false;
  return MARKETING_V2_EXACT.has(pathname);
}
