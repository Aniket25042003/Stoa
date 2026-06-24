/**
 * @file apps/web/src/lib/csp.ts
 * @layer Frontend Shared Utilities
 * @description Single source of truth for Content-Security-Policy (middleware + next.config).
 * @dependencies Supabase
 */

function originFromUrl(url: string | undefined): string {
  if (!url) return "";
  try {
    return new URL(url).origin;
  } catch {
    return "";
  }
}

export type CspOptions = {
  /** Allow unsafe-eval for Next.js dev tooling (off in production). */
  allowUnsafeEval?: boolean;
};

/** Content-Security-Policy for marketing + app surfaces (Next.js compatible). */
export function buildContentSecurityPolicy(options: CspOptions = {}): string {
  const allowUnsafeEval = options.allowUnsafeEval ?? process.env.NODE_ENV !== "production";

  const supabaseOrigin = originFromUrl(process.env.NEXT_PUBLIC_SUPABASE_URL);
  const apiOrigin = originFromUrl(process.env.NEXT_PUBLIC_API_URL ?? process.env.API_URL);

  const connectOrigins = ["'self'", supabaseOrigin, apiOrigin, "https://va.vercel-scripts.com"].filter(
    Boolean,
  );
  const connectSrc = [...new Set(connectOrigins)].join(" ");

  const imgOrigins = [supabaseOrigin].filter(Boolean);
  const imgSrc = ["'self'", "data:", "blob:", ...imgOrigins].join(" ");

  const scriptSrc = allowUnsafeEval
    ? "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://va.vercel-scripts.com"
    : "script-src 'self' 'unsafe-inline' https://va.vercel-scripts.com";

  return [
    "default-src 'self'",
    scriptSrc,
    "style-src 'self' 'unsafe-inline'",
    `img-src ${imgSrc}`,
    "font-src 'self' data:",
    `connect-src ${connectSrc}`,
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "object-src 'none'",
  ].join("; ");
}
