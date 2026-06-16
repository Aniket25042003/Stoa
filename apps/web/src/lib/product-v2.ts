/** Authenticated app surfaces use the marketing cream/indigo design system. */
export const PRODUCT_V2_CLASS = "product-v2";

export function isProductV2Route(pathname: string | null): boolean {
  if (!pathname) return false;
  return (
    pathname === "/login" ||
    pathname.startsWith("/verify-email") ||
    pathname.startsWith("/invite/") ||
    pathname.startsWith("/onboarding") ||
    pathname.startsWith("/dashboard") ||
    pathname.startsWith("/data") ||
    pathname.startsWith("/intelligence") ||
    pathname.startsWith("/competitive") ||
    pathname.startsWith("/campaigns") ||
    pathname.startsWith("/settings")
  );
}
