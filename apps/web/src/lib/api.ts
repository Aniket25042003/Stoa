/**
 * @file apps/web/src/lib/api.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies BFF apiFetch
 */
/** Client-safe API helper — always routes through the BFF proxy. */
export async function apiFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const normalizedPath = path.startsWith("/") ? path.slice(1) : path;
  try {
    return await fetch(`/api/backend/${normalizedPath}`, { ...init, headers });
  } catch {
    return new Response(JSON.stringify({ detail: "Failed to fetch" }), {
      status: 503,
      headers: { "Content-Type": "application/json" },
    });
  }
}
