/**
 * @file apps/web/src/app/api/auth/signup/route.ts
 * @layer Frontend BFF / API Routes
 * @description Handles browser-facing API requests and forwards them through the server-side boundary.
 * @dependencies standard library / local modules
 */
import { NextResponse } from "next/server";
import { enforceAuthRateLimit } from "@/lib/rate-limit-gate";
import { rejectIfCrossOrigin } from "@/lib/same-origin";
import { proxyJsonResponse } from "@/lib/server-api";

/**
 * Handles post behavior for this part of the Stoa application.
 *
 * @param request - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export async function POST(request: Request) {
  const crossOrigin = rejectIfCrossOrigin(request);
  if (crossOrigin) return crossOrigin;

  const bodyText = await request.text();
  let body: { email?: string };
  try {
    body = JSON.parse(bodyText) as { email?: string };
  } catch {
    return NextResponse.json({ detail: "Invalid request." }, { status: 400 });
  }

  const email = String(body.email ?? "").trim().toLowerCase();
  if (!email) {
    return NextResponse.json({ detail: "Email is required." }, { status: 400 });
  }

  const rateLimited = await enforceAuthRateLimit(request, email, "auth_signup");
  if (rateLimited) return rateLimited;

  return proxyJsonResponse(request, "/v1/auth/signup", { method: "POST", body: bodyText });
}
