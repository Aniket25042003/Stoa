/**
 * @file apps/web/src/app/api/auth/session/route.ts
 * @layer Frontend BFF / API Routes
 * @description Handles browser-facing API requests and forwards them through the server-side boundary.
 * @dependencies Supabase, Next.js
 */
import { NextResponse } from "next/server";
import { getServerApiBase } from "@/lib/server-api";
import { createClient } from "@/lib/supabase/server";

/**
 * Handles get behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export async function GET() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    return NextResponse.json({ authenticated: false });
  }

  const apiBase = getServerApiBase();
  if (!apiBase) {
    return NextResponse.json({
      authenticated: true,
      email: session.user.email ?? null,
    });
  }

  try {
    const res = await fetch(`${apiBase}/v1/auth/session-state`, {
      headers: { Authorization: `Bearer ${session.access_token}` },
      cache: "no-store",
    });
    if (!res.ok) {
      return NextResponse.json({
        authenticated: true,
        email: session.user.email ?? null,
      });
    }
    return NextResponse.json({
      authenticated: true,
      ...(await res.json()),
    });
  } catch {
    return NextResponse.json({
      authenticated: true,
      email: session.user.email ?? null,
    });
  }
}
