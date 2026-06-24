/**
 * @file apps/web/src/app/api/auth/oauth/route.ts
 * @layer Frontend BFF / API Routes
 * @description Handles browser-facing API requests and forwards them through the server-side boundary.
 * @dependencies Supabase, Next.js
 */
import { NextResponse } from "next/server";
import { safeNextPath } from "@/lib/auth-workflow";
import { rejectIfCrossOrigin } from "@/lib/same-origin";
import { createClient } from "@/lib/supabase/server";

function isProductionRuntime(): boolean {
  return (
    process.env.VERCEL_ENV === "production" ||
    (process.env.NODE_ENV === "production" && process.env.VERCEL_ENV !== "preview")
  );
}

function oauthRedirectOrigin(request: Request): string | null {
  if (isProductionRuntime()) {
    const configured = process.env.NEXT_PUBLIC_APP_URL?.replace(/\/$/, "");
    return configured ?? null;
  }
  return request.headers.get("origin") ?? process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";
}

/**
 * Handles post behavior for this part of the Stoa application.
 *
 * @param request - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export async function POST(request: Request) {
  const crossOrigin = rejectIfCrossOrigin(request);
  if (crossOrigin) return crossOrigin;

  let body: { provider?: string; next?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ detail: "Invalid request." }, { status: 400 });
  }

  const provider = body.provider === "azure" ? "azure" : body.provider === "google" ? "google" : null;
  if (!provider) {
    return NextResponse.json({ detail: "Unsupported provider." }, { status: 400 });
  }

  const next = safeNextPath(body.next);
  const origin = oauthRedirectOrigin(request);
  if (!origin) {
    return NextResponse.json({ detail: "App URL is not configured." }, { status: 503 });
  }
  const redirectTo = `${origin}/auth/callback?next=${encodeURIComponent(next)}`;

  const supabase = await createClient();
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider,
    options: provider === "azure" ? { redirectTo, scopes: "email" } : { redirectTo },
  });

  if (error || !data.url) {
    return NextResponse.json(
      { detail: error?.message ?? `Could not start ${provider === "azure" ? "Microsoft" : "Google"} sign-in.` },
      { status: 400 },
    );
  }

  return NextResponse.json({ url: data.url });
}
