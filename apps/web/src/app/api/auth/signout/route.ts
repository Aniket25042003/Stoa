/**
 * @file apps/web/src/app/api/auth/signout/route.ts
 * @layer Frontend BFF / API Routes
 * @description Handles browser-facing API requests and forwards them through the server-side boundary.
 * @dependencies Supabase, Next.js
 */
import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

/**
 * Handles post behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export async function POST() {
  const supabase = await createClient();
  const { error } = await supabase.auth.signOut();
  if (error) {
    return NextResponse.json({ detail: error.message }, { status: 400 });
  }
  return NextResponse.json({ status: "ok" });
}
