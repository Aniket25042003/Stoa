/**
 * @file apps/web/src/lib/bff-auth.ts
 * @layer Frontend BFF / API Routes
 * @description Validates Supabase session server-side before forwarding bearer tokens upstream.
 */
import { createClient } from "@/lib/supabase/server";

export type BffAuthResult =
  | { ok: true; accessToken: string; userId: string }
  | { ok: false; status: 401; detail: string };

/**
 * Validates identity with Auth server, then reads the access token for upstream API calls.
 */
export async function getBffAccessToken(): Promise<BffAuthResult> {
  const supabase = await createClient();
  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser();

  if (!user || userError) {
    return { ok: false, status: 401, detail: "Not authenticated" };
  }

  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    return { ok: false, status: 401, detail: "Not authenticated" };
  }

  return { ok: true, accessToken: session.access_token, userId: user.id };
}
