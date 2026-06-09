"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import type { EmailOtpType } from "@supabase/supabase-js";
import { apiFetch } from "@/lib/api";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { routeForSessionState, safeNextPath, type SessionState } from "@/lib/auth-workflow";
import { createClient } from "@/lib/supabase/client";

export function AuthCallbackClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [message, setMessage] = useState("Signing you in...");

  useEffect(() => {
    const next = safeNextPath(searchParams.get("next"));
    const authEntry = getAuthEntryPath();

    void (async () => {
      const supabase = createClient();
      const code = searchParams.get("code");
      const token_hash = searchParams.get("token_hash");
      const type = searchParams.get("type");

      if (token_hash && type) {
        const { error } = await supabase.auth.verifyOtp({
          type: type as EmailOtpType,
          token_hash,
        });
        if (error) {
          router.replace(`${authEntry}?error=${encodeURIComponent(error.message)}`);
          return;
        }
      } else if (code) {
        const { error } = await supabase.auth.exchangeCodeForSession(code);
        if (error) {
          router.replace(`${authEntry}?error=${encodeURIComponent(error.message)}`);
          return;
        }
      }

      const {
        data: { user },
        error: userError,
      } = await supabase.auth.getUser();

      if (userError || !user) {
        setMessage("Could not establish a session. Try signing in again.");
        router.replace(`${authEntry}?error=session`);
        return;
      }

      const res = await apiFetch("/v1/auth/session-state");
      if (res.ok) {
        const state = (await res.json()) as SessionState;
        router.replace(routeForSessionState(state, next));
        return;
      }

      router.replace(next);
    })();
  }, [router, searchParams]);

  return (
    <div className="flex min-h-screen items-center justify-center px-4 text-sm text-on-surface-variant">{message}</div>
  );
}
