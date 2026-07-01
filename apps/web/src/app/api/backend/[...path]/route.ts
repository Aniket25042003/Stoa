/**
 * @file apps/web/src/app/api/backend/[...path]/route.ts
 * @layer Frontend BFF / API Routes
 * @description Handles browser-facing API requests and forwards them through the server-side boundary.
 * @dependencies Supabase, Next.js
 */
import { getBffAccessToken } from "@/lib/bff-auth";
import { trustedProxyHeaders } from "@/lib/proxy-headers";
import { rejectIfCrossOrigin } from "@/lib/same-origin";
import { NextRequest, NextResponse } from "next/server";

const apiBase = () => {
  const value = process.env.NEXT_PUBLIC_API_URL;
  if (!value) throw new Error("NEXT_PUBLIC_API_URL is not set");
  return value.replace(/\/$/, "");
};

/**
 * Handles proxy behavior for this part of the Stoa application.
 *
 * @param request - Input value used to render UI or execute the workflow.
 * @param pathSegments - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
async function proxy(request: NextRequest, pathSegments: string[]) {
  if (request.method !== "GET" && request.method !== "HEAD") {
    const forbidden = rejectIfCrossOrigin(request);
    if (forbidden) return forbidden;
  }

  const auth = await getBffAccessToken();
  if (!auth.ok) {
    return NextResponse.json({ detail: auth.detail }, { status: auth.status });
  }

  const path = pathSegments.join("/");
  const target = `${apiBase()}/${path}${request.nextUrl.search}`;
  const headers = new Headers();
  headers.set("Authorization", `Bearer ${auth.accessToken}`);
  for (const [key, value] of Object.entries(trustedProxyHeaders(request))) {
    headers.set(key, value);
  }
  const orgId = request.cookies.get("stoa-active-org")?.value;
  if (orgId) headers.set("X-Org-Id", orgId);
  const accept = request.headers.get("accept");
  if (accept) headers.set("Accept", accept);
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("Content-Type", contentType);

  const init: RequestInit = {
    method: request.method,
    headers,
    cache: "no-store",
  };

  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = request.body;
    // @ts-expect-error duplex required for streaming bodies in Node 18+
    init.duplex = "half";
  }

  let upstream: Response;
  try {
    upstream = await fetch(target, init);
  } catch {
    return NextResponse.json({ detail: "Upstream API unreachable" }, { status: 503 });
  }

  if (accept?.includes("text/event-stream") && upstream.body) {
    return new NextResponse(upstream.body, {
      status: upstream.status,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  }

  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") ?? "application/json",
    },
  });
}

type RouteContext = { params: Promise<{ path: string[] }> };

/**
 * Handles get behavior for this part of the Stoa application.
 *
 * @param request - Input value used to render UI or execute the workflow.
 * @param context - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export async function GET(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  return proxy(request, path);
}

/**
 * Handles post behavior for this part of the Stoa application.
 *
 * @param request - Input value used to render UI or execute the workflow.
 * @param context - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export async function POST(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  return proxy(request, path);
}

/**
 * Handles patch behavior for this part of the Stoa application.
 *
 * @param request - Input value used to render UI or execute the workflow.
 * @param context - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export async function PATCH(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  return proxy(request, path);
}

/**
 * Handles put behavior for this part of the Stoa application.
 *
 * @param request - Input value used to render UI or execute the workflow.
 * @param context - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export async function PUT(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  return proxy(request, path);
}

/**
 * Handles delete behavior for this part of the Stoa application.
 *
 * @param request - Input value used to render UI or execute the workflow.
 * @param context - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export async function DELETE(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  return proxy(request, path);
}
