import { ACTIVE_ORG_COOKIE } from "@/lib/active-org";
import { trustedProxyHeaders } from "@/lib/proxy-headers";

function activeOrgFromRequest(request: Request): string | null {
  const cookie = request.headers.get("cookie") ?? "";
  const match = cookie.match(new RegExp(`(?:^|;\\s*)${ACTIVE_ORG_COOKIE}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

export function getServerApiBase(): string | null {
  const value = process.env.NEXT_PUBLIC_API_URL;
  if (!value) return null;
  return value.replace(/\/$/, "");
}

export async function proxyToApi(request: Request, path: string, init?: RequestInit) {
  const base = getServerApiBase();
  if (!base) {
    return new Response(JSON.stringify({ detail: "API URL is not configured." }), {
      status: 503,
      headers: { "Content-Type": "application/json" },
    });
  }

  const method = init?.method ?? request.method;
  const body =
    init?.body !== undefined
      ? init.body
      : method !== "GET" && method !== "HEAD"
        ? await request.text()
        : undefined;

  const orgId = activeOrgFromRequest(request);

  try {
    return await fetch(`${base}${path}`, {
      ...init,
      method,
      headers: {
        "Content-Type": "application/json",
        Origin: request.headers.get("origin") ?? "",
        ...trustedProxyHeaders(request),
        ...(orgId ? { "X-Org-Id": orgId } : {}),
        ...(init?.headers ?? {}),
      },
      body,
      cache: "no-store",
    });
  } catch {
    return new Response(
      JSON.stringify({
        detail: "Service temporarily unavailable. Start the API server with: uvicorn app.main:app --reload --port 8000",
      }),
      { status: 503, headers: { "Content-Type": "application/json" } },
    );
  }
}

export async function proxyJsonResponse(request: Request, path: string, init?: RequestInit) {
  const upstream = await proxyToApi(request, path, init);
  const text = await upstream.text();
  return new Response(text, {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json" },
  });
}
