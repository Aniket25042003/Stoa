/**
 * @file apps/web/src/app/api/auth/signin/route.ts
 * @layer Frontend BFF / API Routes
 * @description Handles browser-facing API requests and forwards them through the server-side boundary.
 * @dependencies Supabase, Next.js
 */
import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { enforceAuthRateLimit } from "@/lib/rate-limit-gate";

/**
 * Handles post behavior for this part of the Stoa application.
 *
 * @param request - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export async function POST(request: Request) {
  let body: { email?: string; password?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ detail: "Invalid request." }, { status: 400 });
  }

  const email = String(body.email ?? "").trim().toLowerCase();
  const password = String(body.password ?? "");
  if (!email || !password) {
    return NextResponse.json({ detail: "Email and password are required." }, { status: 400 });
  }

  const rateLimited = await enforceAuthRateLimit(request, email, "auth_signin");
  if (rateLimited) return rateLimited;

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) {
    const needsVerify = error.message.toLowerCase().includes("confirm");
    return NextResponse.json(
      {
        detail: needsVerify
          ? "Confirm your email before signing in."
          : "Invalid email or password.",
        needs_email_verification: needsVerify,
      },
      { status: needsVerify ? 403 : 400 },
    );
  }

  return NextResponse.json({ status: "ok" });
}
