"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { routeForSessionState, safeNextPath, type SessionState } from "@/lib/auth-workflow";
import { BRAND_NAME } from "@/lib/brand";

function VerifyEmailClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState(searchParams.get("email") ?? "");
  const [message, setMessage] = useState<string | null>(null);
  const [resending, setResending] = useState(false);
  const next = safeNextPath(searchParams.get("next"));

  useEffect(() => {
    let cancelled = false;

    async function checkSession() {
      const res = await fetch("/api/auth/session");
      if (!res.ok || cancelled) return;
      const state = (await res.json()) as SessionState & { authenticated?: boolean; email?: string | null };
      if (state.email) setEmail(state.email);
      if (!state.authenticated) return;
      if (!state.needs_email_verification) {
        router.replace(routeForSessionState(state, next));
        router.refresh();
      }
    }

    void checkSession();
    const interval = window.setInterval(() => void checkSession(), 4000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [next, router]);

  async function resend() {
    setMessage(null);
    if (!email) {
      setMessage("Enter your email first.");
      return;
    }
    setResending(true);
    const res = await fetch("/api/auth/resend-verification", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, next }),
    });
    const body = (await res.json().catch(() => null)) as { detail?: string } | null;
    setResending(false);
    if (res.ok) {
      setMessage("Verification link sent. Open the email and click the link to continue.");
    } else {
      setMessage(body?.detail || "Could not send verification email. Check Supabase Auth logs and Brevo SMTP settings.");
    }
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
              We sent a confirmation link to your email. Click it to verify your account — you will be signed in and taken into the app automatically.
            </p>
          </div>
          <div className="mt-6 space-y-4">
            <div>
              <label className="text-sm font-medium">Email</label>
              <input
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                type="email"
                required
                autoComplete="email"
                className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm"
                placeholder="you@company.com"
              />
            </div>
            <button
              type="button"
              onClick={() => void resend()}
              disabled={resending}
              className="btn-primary w-full px-5 py-3 text-sm disabled:opacity-50"
            >
              {resending ? "Sending..." : "Resend verification link"}
            </button>
            <p className="text-xs leading-6 text-on-surface-variant">
              Already clicked the link? This page will redirect you automatically once verification completes.
            </p>
          </div>
          {message ? <p className="mt-4 text-sm text-on-surface-variant">{message}</p> : null}
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
