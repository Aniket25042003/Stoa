/**
 * @file apps/web/src/app/auth/callback/route.ts
 * @layer Application Source
 * @description Implements route behavior for the application source.
 * @dependencies Supabase, Next.js
 */
import type { EmailOtpType } from "@supabase/supabase-js";
import { NextResponse } from "next/server";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { routeForSessionState, safeNextPath, type SessionState } from "@/lib/auth-workflow";
import { getServerApiBase } from "@/lib/server-api";
import { createClient } from "@/lib/supabase/server";

/**
 * Handles get behavior for this part of the Stoa application.
 *
 * @param request - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export async function GET(request: Request) {
  const url = new URL(request.url);
  const authEntry = getAuthEntryPath({ hostname: url.hostname });
  const next = safeNextPath(url.searchParams.get("next"));
  const code = url.searchParams.get("code");
  const tokenHash = url.searchParams.get("token_hash");
  const type = url.searchParams.get("type");

  const supabase = await createClient();

  if (tokenHash && type) {
    const { error } = await supabase.auth.verifyOtp({
      type: type as EmailOtpType,
      token_hash: tokenHash,
    });
    if (error) {
      return NextResponse.redirect(new URL(`${authEntry}?error=${encodeURIComponent(error.message)}`, request.url));
    }
  } else if (code) {
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (error) {
      return NextResponse.redirect(new URL(`${authEntry}?error=${encodeURIComponent(error.message)}`, request.url));
    }
  }

  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser();

  if (userError || !user) {
    return NextResponse.redirect(new URL(`${authEntry}?error=session`, request.url));
  }

  const {
    data: { session },
  } = await supabase.auth.getSession();

  const apiBase = getServerApiBase();
  if (apiBase && session?.access_token) {
    try {
      const res = await fetch(`${apiBase}/v1/auth/session-state`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
        cache: "no-store",
      });
      if (res.ok) {
        const state = (await res.json()) as SessionState;
        const dest = routeForSessionState(state, next);
        return NextResponse.redirect(new URL(dest, request.url));
      }
    } catch {
      // Fall through to default redirect.
    }
  }

  return NextResponse.redirect(new URL(next, request.url));
}
