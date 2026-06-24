/**
 * @file apps/web/src/lib/same-origin.ts
 * @layer Frontend Shared Utilities
 * @description Same-origin validation for sensitive BFF POST routes (CSRF mitigation).
 */

function isProductionRuntime(): boolean {
  return (
    process.env.VERCEL_ENV === "production" ||
    (process.env.NODE_ENV === "production" && process.env.VERCEL_ENV !== "preview")
  );
}

function allowedOrigins(): Set<string> {
  const origins = new Set<string>();
  const appUrl = process.env.NEXT_PUBLIC_APP_URL?.replace(/\/$/, "");
  if (appUrl) {
    try {
      origins.add(new URL(appUrl).origin);
    } catch {
      /* ignore malformed */
    }
  }
  if (process.env.VERCEL_URL) {
    origins.add(`https://${process.env.VERCEL_URL}`);
  }
  if (!isProductionRuntime()) {
    origins.add("http://localhost:3000");
    origins.add("http://127.0.0.1:3000");
  }
  return origins;
}

function forbiddenResponse(): Response {
  return new Response(JSON.stringify({ detail: "Forbidden." }), {
    status: 403,
    headers: { "Content-Type": "application/json" },
  });
}

/** Reject cross-origin POSTs when Origin/Referer do not match the app. */
export function rejectIfCrossOrigin(request: Request): Response | null {
  const allowed = allowedOrigins();
  if (allowed.size === 0) {
    return isProductionRuntime() ? forbiddenResponse() : null;
  }

  const origin = request.headers.get("origin");
  if (origin) {
    return allowed.has(origin) ? null : forbiddenResponse();
  }

  const referer = request.headers.get("referer");
  if (referer) {
    try {
      return allowed.has(new URL(referer).origin) ? null : forbiddenResponse();
    } catch {
      return forbiddenResponse();
    }
  }

  return isProductionRuntime() ? forbiddenResponse() : null;
}
