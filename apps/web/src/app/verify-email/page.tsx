"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { routeForSessionState, safeNextPath, type SessionState } from "@/lib/auth-workflow";
import { BRAND_NAME } from "@/lib/brand";
import { createClient } from "@/lib/supabase/client";

function VerifyEmailClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState(searchParams.get("email") ?? "");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const next = safeNextPath(searchParams.get("next"));

  useEffect(() => {
    void (async () => {
      const supabase = createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (user?.email) setEmail(user.email);
      if (!user) return;
      const res = await apiFetch("/v1/auth/session-state");
      if (res.ok) {
        const state = (await res.json()) as SessionState;
        if (!state.needs_email_verification) {
          router.replace(routeForSessionState(state, next));
        }
      }
    })();
  }, [next, router]);

  async function resend() {
    setMessage(null);
    if (!email) {
      setMessage("Enter your email first.");
      return;
    }
    setLoading(true);
    const supabase = createClient();
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    const emailRedirectTo = `${origin}/auth/callback?next=${encodeURIComponent(next)}`;
    const { error } = await supabase.auth.resend({
      type: "signup",
      email,
      options: { emailRedirectTo },
    });
    setLoading(false);
    setMessage(error ? error.message : "Verification email sent. Check your inbox.");
  }

  return (
    <div className="relative min-h-screen overflow-hidden px-4 py-10 md:px-6">
      <div className="absolute inset-0 -z-10 grid-bg dark:starfield" />
      <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-xl items-center">
        <div className="w-full rounded-3xl p-7 card-glass md:p-8">
          <Link href="/" className="inline-flex items-center gap-3">
            <span className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary to-violet-pulse shadow-glow" />
            <span className="font-display text-xl font-extrabold tracking-[-0.03em] text-on-surface">{BRAND_NAME}</span>
          </Link>
          <div className="mt-8 rounded-2xl bg-slate-deep p-5 text-white shadow-card">
            <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-inverse-primary">Verify email</p>
            <h1 className="mt-2 font-display text-2xl font-bold tracking-[-0.03em]">Check your inbox</h1>
            <p className="mt-2 text-sm leading-6 text-white/68">
              Supabase sent your verification email through the configured Brevo SMTP sender. Open the link to continue setup.
            </p>
          </div>
          <div className="mt-6 space-y-4">
            <label className="text-sm font-medium">Email</label>
            <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" className="w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="you@company.com" />
            <button type="button" onClick={() => void resend()} disabled={loading} className="btn-primary w-full px-5 py-3 text-sm disabled:opacity-50">
              {loading ? "Sending..." : "Resend verification email"}
            </button>
            {message ? <p className="text-sm text-on-surface-variant">{message}</p> : null}
          </div>
          <p className="mt-7 text-center text-sm">
            <Link href={`/login?next=${encodeURIComponent(next)}`} className="font-bold text-primary underline-offset-4 hover:underline">
              Back to sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center px-4 text-sm text-on-surface-variant">Loading...</div>}>
      <VerifyEmailClient />
    </Suspense>
  );
}
