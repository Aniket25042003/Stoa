/**
 * @file apps/web/src/app/api/orgs/switch/route.ts
 * @layer Frontend BFF / API Routes
 * @description Handles browser-facing API requests and forwards them through the server-side boundary.
 * @dependencies Next.js
 */
import { NextResponse } from "next/server";
import { ACTIVE_ORG_COOKIE } from "@/lib/active-org";
import { rejectIfCrossOrigin } from "@/lib/same-origin";
import { proxyAuthenticatedJsonResponse } from "@/lib/server-api";

/**
 * Handles post behavior for this part of the Stoa application.
 *
 * @param request - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export async function POST(request: Request) {
  const forbidden = rejectIfCrossOrigin(request);
  if (forbidden) return forbidden;

  const upstream = await proxyAuthenticatedJsonResponse(request, "/v1/orgs/switch");
  const text = await upstream.text();
  if (!upstream.ok) {
    return new Response(text, { status: upstream.status, headers: { "Content-Type": "application/json" } });
  }
  let body: { active_org_id?: string } = {};
  try {
    body = JSON.parse(text) as { active_org_id?: string };
  } catch {
    return NextResponse.json({ detail: "Invalid response." }, { status: 502 });
  }
  const response = NextResponse.json(body);
  if (body.active_org_id) {
    response.cookies.set(ACTIVE_ORG_COOKIE, body.active_org_id, {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: 60 * 60 * 24 * 365,
    });
  }
  return response;
}
