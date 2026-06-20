/**
 * @file apps/web/src/lib/api-server.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies BFF apiFetch
 */
import { getServerActiveOrgId } from "@/lib/active-org-server";

const serverApiBase = () => {
  const b = process.env.NEXT_PUBLIC_API_URL;
  if (!b) throw new Error("NEXT_PUBLIC_API_URL is not set");
  return b.replace(/\/$/, "");
};

/** Server Component / route handler API helper with JWT + active org. */
export async function apiFetchServer(
  path: string,
  init: RequestInit & { accessToken?: string } = {},
) {
  const { accessToken, ...rest } = init;
  const headers = new Headers(rest.headers);
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  const orgId = await getServerActiveOrgId();
  if (orgId) headers.set("X-Org-Id", orgId);
  if (!headers.has("Content-Type") && !(rest.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const normalizedPath = path.startsWith("/") ? path.slice(1) : path;
  const res = await fetch(`${serverApiBase()}/${normalizedPath}`, { ...rest, headers, cache: "no-store" });
  return res;
}
