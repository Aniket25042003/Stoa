"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import type { EmailOtpType } from "@supabase/supabase-js";
import { createClient } from "@/lib/supabase/client";

export function AuthCallbackClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [message, setMessage] = useState("Signing you in…");

  useEffect(() => {
    const rawNext = searchParams.get("next") ?? "/dashboard";
    const next = rawNext.startsWith("/") ? rawNext : "/dashboard";

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
          router.replace(`/login?error=${encodeURIComponent(error.message)}`);
          return;
        }
      } else if (code) {
        // Ignore exchange errors (e.g. code already consumed in React Strict Mode); final getSession decides.
        await supabase.auth.exchangeCodeForSession(code);
      }

      const {
        data: { session },
        error: sessionError,
      } = await supabase.auth.getSession();

      if (sessionError || !session) {
        setMessage("Could not establish a session. Try signing in again.");
        router.replace("/login?error=session");
        return;
      }

      router.replace(next);
    })();
  }, [router, searchParams]);

  return (
    <div className="flex min-h-screen items-center justify-center px-4 text-sm text-ink/70">{message}</div>
  );
}
