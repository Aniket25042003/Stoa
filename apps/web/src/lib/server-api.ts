/**
 * @file apps/web/src/lib/server-api.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
import { ACTIVE_ORG_COOKIE } from "@/lib/active-org";
import { getBffAccessToken } from "@/lib/bff-auth";
import { trustedProxyHeaders } from "@/lib/proxy-headers";

const UPSTREAM_TIMEOUT_MS = 25_000;
const UPSTREAM_RETRIES = 2;
const UPSTREAM_RETRY_DELAY_MS = 2_000;

/**
 * Handles active org from request behavior for this part of the Stoa application.
 *
 * @param request - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
function activeOrgFromRequest(request: Request): string | null {
  const cookie = request.headers.get("cookie") ?? "";
  const match = cookie.match(new RegExp(`(?:^|;\\s*)${ACTIVE_ORG_COOKIE}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

/**
 * Handles is production runtime behavior for this part of the Stoa application.
 * @returns Result consumed by the caller or rendered by React.
 */
function isProductionRuntime(): boolean {
  return (
    process.env.VERCEL_ENV === "production" ||
    (process.env.NODE_ENV === "production" && process.env.VERCEL_ENV !== "preview")
  );
}

/**
 * Handles is loopback api url behavior for this part of the Stoa application.
 *
 * @param base - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
function isLoopbackApiUrl(base: string): boolean {
  try {
    const host = new URL(base).hostname.toLowerCase();
    return host === "localhost" || host === "127.0.0.1" || host === "[::1]";
  } catch {
    return true;
  }
}

/** Server-side API base URL. Prefer API_URL; NEXT_PUBLIC_API_URL is the public fallback. */
export function getServerApiBase(): string | null {
  const value = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL;
  if (!value) return null;
  const base = value.replace(/\/$/, "");
  if (isProductionRuntime() && isLoopbackApiUrl(base)) return null;
  return base;
}

/**
 * Handles upstream unavailable message behavior for this part of the Stoa application.
 * @returns Result consumed by the caller or rendered by React.
 */
function upstreamUnavailableMessage(): string {
  if (isProductionRuntime()) {
    return "Waitlist is temporarily unavailable. Please try again in a moment.";
  }
  return "Service temporarily unavailable. Start the API server with: uvicorn app.main:app --reload --port 8000";
}

/**
 * Handles misconfigured api message behavior for this part of the Stoa application.
 * @returns Result consumed by the caller or rendered by React.
 */
function misconfiguredApiMessage(): string {
  if (isProductionRuntime()) {
    return "API URL is not configured for production. Set API_URL (or NEXT_PUBLIC_API_URL) to your Render service URL on Vercel, then redeploy.";
  }
  return "API URL is not configured.";
}

/**
 * Handles sleep behavior for this part of the Stoa application.
 *
 * @param ms - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
async function sleep(ms: number): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Handles fetch upstream behavior for this part of the Stoa application.
 *
 * @param url - Input value used to render UI or execute the workflow.
 * @param init - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
async function fetchUpstream(url: string, init: RequestInit): Promise<Response> {
  let lastError: unknown;
  for (let attempt = 0; attempt <= UPSTREAM_RETRIES; attempt += 1) {
    try {
      return await fetch(url, {
        ...init,
        signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
      });
    } catch (error) {
      lastError = error;
      if (attempt < UPSTREAM_RETRIES) {
        await sleep(UPSTREAM_RETRY_DELAY_MS);
      }
    }
  }
  throw lastError;
}

/**
 * Handles proxy to api behavior for this part of the Stoa application.
 *
 * @param request - Input value used to render UI or execute the workflow.
 * @param path - Input value used to render UI or execute the workflow.
 * @param init - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export async function proxyToApi(
  request: Request,
  path: string,
  init?: RequestInit,
  options?: { accessToken?: string },
) {
  const base = getServerApiBase();
  if (!base) {
    return new Response(JSON.stringify({ detail: misconfiguredApiMessage() }), {
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
    return await fetchUpstream(`${base}${path}`, {
      ...init,
      method,
      headers: {
        "Content-Type": "application/json",
        Origin: request.headers.get("origin") ?? process.env.NEXT_PUBLIC_APP_URL ?? "",
        ...trustedProxyHeaders(request),
        ...(orgId ? { "X-Org-Id": orgId } : {}),
        ...(options?.accessToken ? { Authorization: `Bearer ${options.accessToken}` } : {}),
        ...(init?.headers ?? {}),
      },
      body,
      cache: "no-store",
    });
  } catch {
    return new Response(JSON.stringify({ detail: upstreamUnavailableMessage() }), {
      status: 503,
      headers: { "Content-Type": "application/json" },
    });
  }
}

/**
 * Handles proxy json response behavior for this part of the Stoa application.
 *
 * @param request - Input value used to render UI or execute the workflow.
 * @param path - Input value used to render UI or execute the workflow.
 * @param init - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export async function proxyJsonResponse(
  request: Request,
  path: string,
  init?: RequestInit,
  options?: { accessToken?: string },
) {
  const upstream = await proxyToApi(request, path, init, options);
  const text = await upstream.text();
  return new Response(text, {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json" },
  });
}

/** Proxy to the API with the current Supabase session bearer token (required for auth routes). */
export async function proxyAuthenticatedJsonResponse(
  request: Request,
  path: string,
  init?: RequestInit,
) {
  const auth = await getBffAccessToken();
  if (!auth.ok) {
    return new Response(JSON.stringify({ detail: auth.detail }), {
      status: auth.status,
      headers: { "Content-Type": "application/json" },
    });
  }
  return proxyJsonResponse(request, path, init, { accessToken: auth.accessToken });
}
