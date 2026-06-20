/**
 * @file apps/web/src/lib/proxy-headers.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
export function clientIpFromRequest(request: Request): string {
  const forwarded = request.headers.get("x-forwarded-for");
  if (forwarded) {
    const part = forwarded.split(",")[0]?.trim();
    if (part) return part;
  }
  const realIp = request.headers.get("x-real-ip")?.trim();
  if (realIp) return realIp;
  return "unknown";
}

/**
 * Handles trusted proxy headers behavior for this part of the Stoa application.
 *
 * @param request - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
export function trustedProxyHeaders(request: Request): Record<string, string> {
  const headers: Record<string, string> = {
    "X-Stoa-Client-IP": clientIpFromRequest(request),
  };
  const secret = process.env.INTERNAL_PROXY_SECRET;
  if (secret) {
    headers["X-Stoa-Proxy-Secret"] = secret;
  }
  return headers;
}
