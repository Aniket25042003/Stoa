/**
 * @file apps/web/src/lib/api-server.ts
 * @layer Frontend Shared Utilities
 * @description Server Component / route handler API helper with JWT + active org.
 */
import { headers } from "next/headers";
import { getServerActiveOrgId } from "@/lib/active-org-server";
import { trustedProxyHeaders, trustedProxyHeadersFromHeaders } from "@/lib/proxy-headers";

const serverApiBase = () => {
  const b = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL;
  if (!b) throw new Error("API_URL or NEXT_PUBLIC_API_URL is not set");
  return b.replace(/\/$/, "");
};

/** Server Component / route handler API helper with JWT + active org. */
export async function apiFetchServer(
  path: string,
  init: RequestInit & { accessToken?: string; request?: Request } = {},
) {
  const { accessToken, request, ...rest } = init;
  const headersInit = new Headers(rest.headers);
  if (accessToken) {
    headersInit.set("Authorization", `Bearer ${accessToken}`);
  }
  const proxyHdrs = request
    ? trustedProxyHeaders(request)
    : trustedProxyHeadersFromHeaders(await headers());
  for (const [key, value] of Object.entries(proxyHdrs)) {
    headersInit.set(key, value);
  }
  const orgId = await getServerActiveOrgId();
  if (orgId) headersInit.set("X-Org-Id", orgId);
  if (!headersInit.has("Content-Type") && !(rest.body instanceof FormData)) {
    headersInit.set("Content-Type", "application/json");
  }
  const normalizedPath = path.startsWith("/") ? path.slice(1) : path;
  const res = await fetch(`${serverApiBase()}/${normalizedPath}`, {
    ...rest,
    headers: headersInit,
    cache: "no-store",
  });
  return res;
}
