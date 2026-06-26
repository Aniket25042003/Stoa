/**
 * @file apps/web/src/lib/product-v2.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
/** Authenticated app surfaces use the marketing cream/indigo design system. */
export const PRODUCT_V2_CLASS = "product-v2";

/**
 * Handles is product v2 route behavior for this part of the Stoa application.
 *
 * @param pathname - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
export function isProductV2Route(pathname: string | null): boolean {
  if (!pathname) return false;
  return (
    pathname === "/login" ||
    pathname.startsWith("/verify-email") ||
    pathname.startsWith("/invite/") ||
    pathname.startsWith("/onboarding") ||
    pathname.startsWith("/dashboard") ||
    pathname.startsWith("/data") ||
    pathname.startsWith("/agent") ||
    pathname.startsWith("/intelligence") ||
    pathname.startsWith("/competitive") ||
    pathname.startsWith("/campaigns") ||
    pathname.startsWith("/settings")
  );
}
