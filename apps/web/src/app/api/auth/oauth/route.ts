import { NextResponse } from "next/server";
import { safeNextPath } from "@/lib/auth-workflow";
import { createClient } from "@/lib/supabase/server";

export async function POST(request: Request) {
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
  const origin = request.headers.get("origin") ?? process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";
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
