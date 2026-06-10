"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { routeForSessionState, safeNextPath, type SessionState } from "@/lib/auth-workflow";
import { ActivityTickerTeaser } from "@/components/marketing/ActivityTickerTeaser";
import { BRAND_NAME, BRAND_SUBHEAD, BRAND_TAGLINE } from "@/lib/brand";

function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden>
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
    </svg>
  );
}

function LoginForm() {
  const searchParams = useSearchParams();
  const [msg, setMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const next = safeNextPath(searchParams.get("next"));

  useEffect(() => {
    const err = searchParams.get("error");
    if (err) setMsg(err);
  }, [searchParams]);

  async function postAuthRoute() {
    const res = await fetch("/api/auth/session");
    if (!res.ok) return next;
    const state = (await res.json()) as SessionState & { authenticated?: boolean };
    if (!state.authenticated) return next;
    return routeForSessionState(state, next);
  }

  async function signInWithProvider(provider: "google" | "azure") {
    setMsg(null);
    setLoading(true);

    const res = await fetch("/api/auth/oauth", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider, next }),
    });
    const body = (await res.json().catch(() => null)) as { url?: string; detail?: string } | null;

    if (!res.ok || !body?.url) {
      setLoading(false);
      setMsg(body?.detail || `Could not start ${provider === "azure" ? "Microsoft" : "Google"} sign-in. Try again.`);
      return;
    }

    window.location.assign(body.url);
  }

  function authErrorMessage(err: unknown, fallback: string): string {
    if (err instanceof Error) {
      const message = err.message.trim();
      if (message && message !== "{}") return message;
    }
    return fallback;
  }

  async function submitEmail(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMsg(null);
    setLoading(true);
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim().toLowerCase();
    const password = String(form.get("password") ?? "");
    const fullName = String(form.get("full_name") ?? "").trim();

    try {
      if (mode === "signup") {
        if (!fullName) {
          setMsg("Full name is required.");
          setLoading(false);
          return;
        }
        const res = await fetch("/api/auth/signup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password, full_name: fullName, next }),
        });
        const body = (await res.json().catch(() => null)) as { detail?: string; status?: string } | null;
        if (!res.ok) {
          throw new Error(body?.detail || "Could not create account. Try again.");
        }
        if (body?.status === "created_email_pending" && body.detail) {
          setMsg(body.detail);
        }
        window.location.assign(`/verify-email?email=${encodeURIComponent(email)}&next=${encodeURIComponent(next)}`);
        return;
      }

      const signInRes = await fetch("/api/auth/signin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const signInBody = (await signInRes.json().catch(() => null)) as {
        detail?: string;
        needs_email_verification?: boolean;
      } | null;
      if (!signInRes.ok) {
        if (signInBody?.needs_email_verification) {
          window.location.assign(`/verify-email?email=${encodeURIComponent(email)}&next=${encodeURIComponent(next)}`);
          return;
        }
        throw new Error(signInBody?.detail || "Could not sign in. Try again.");
      }
      window.location.assign(await postAuthRoute());
    } catch (err) {
      setMsg(authErrorMessage(err, mode === "signup" ? "Could not create account. Try again." : "Could not sign in. Try again."));
      setLoading(false);
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden px-4 py-10 md:px-6">
      <div className="absolute inset-0 -z-10 grid-bg dark:starfield" />
      <div className="absolute left-1/2 top-0 -z-10 h-[520px] w-[min(760px,92vw)] -translate-x-1/2 rounded-full bg-gradient-to-r from-primary/20 via-violet-pulse/18 to-transparent blur-3xl" />
      <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-7xl flex-col gap-10 lg:flex-row lg:items-center lg:gap-16">
        <div className="flex-1 space-y-7 lg:max-w-lg">
          <Link href="/" className="inline-flex items-center gap-3">
            <span className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary to-violet-pulse shadow-glow" />
            <span className="font-display text-xl font-extrabold tracking-[-0.03em] text-on-surface">{BRAND_NAME}</span>
          </Link>
          <div>
            <p className="eyebrow">Secure workspace</p>
            <h1 className="mt-4 font-display text-4xl font-extrabold leading-tight tracking-[-0.045em] text-on-surface md:text-5xl">
              {BRAND_TAGLINE}
            </h1>
            <p className="mt-5 text-base leading-8 text-on-surface-variant">{BRAND_SUBHEAD}</p>
            <p className="mt-4 text-sm leading-7 text-on-surface-variant">Sign in with Google, Microsoft, or your work email to open your marketing intelligence workspace.</p>
          </div>
          <div className="hidden lg:block">
            <ActivityTickerTeaser />
          </div>
        </div>

        <div className="flex flex-1 justify-center lg:justify-end">
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
            className="w-full max-w-md rounded-3xl p-7 card-glass md:p-8"
          >
            <div className="mb-8 rounded-2xl bg-slate-deep p-5 text-white shadow-card">
              <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-inverse-primary">Authentication</p>
              <h2 className="mt-2 font-display text-2xl font-bold tracking-[-0.03em]">Continue to dashboard</h2>
              <p className="mt-2 text-sm leading-6 text-white/62">Use SSO or email/password. Email accounts verify through Supabase Auth emails delivered by Brevo SMTP.</p>
            </div>
            <motion.button
              type="button"
              onClick={() => void signInWithProvider("google")}
              disabled={loading}
              className="btn-secondary flex w-full gap-3 px-5 py-3 text-sm disabled:opacity-50"
              whileTap={{ scale: 0.98 }}
            >
              <GoogleIcon className="h-5 w-5 shrink-0" />
              {loading ? "Redirecting..." : "Continue with Google"}
            </motion.button>
            <motion.button
              type="button"
              onClick={() => void signInWithProvider("azure")}
              disabled={loading}
              className="btn-secondary mt-3 flex w-full gap-3 px-5 py-3 text-sm disabled:opacity-50"
              whileTap={{ scale: 0.98 }}
            >
              <span className="grid h-5 w-5 shrink-0 grid-cols-2 gap-0.5" aria-hidden>
                <span className="bg-[#f25022]" />
                <span className="bg-[#7fba00]" />
                <span className="bg-[#00a4ef]" />
                <span className="bg-[#ffb900]" />
              </span>
              {loading ? "Redirecting..." : "Continue with Microsoft"}
            </motion.button>
            <div className="my-6 flex items-center gap-3 text-xs uppercase tracking-[0.16em] text-on-surface-variant">
              <span className="h-px flex-1 bg-outline-variant/60" />
              Work email
              <span className="h-px flex-1 bg-outline-variant/60" />
            </div>
            <form onSubmit={(event) => void submitEmail(event)} className="space-y-4">
              {mode === "signup" ? (
                <div>
                  <label className="text-sm font-medium">Full name</label>
                  <input name="full_name" type="text" required autoComplete="name" className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="Aniket Patel" />
                </div>
              ) : null}
              <div>
                <label className="text-sm font-medium">Email</label>
                <input name="email" type="email" required className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="you@company.com" />
              </div>
              <div>
                <label className="text-sm font-medium">Password</label>
                <input name="password" type="password" required minLength={8} className="mt-1 w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-3 text-sm" placeholder="At least 8 characters" />
              </div>
              <button type="submit" disabled={loading} className="btn-primary w-full px-5 py-3 text-sm disabled:opacity-50">
                {loading ? "Working..." : mode === "signin" ? "Sign in with email" : "Create account"}
              </button>
            </form>
            <button type="button" onClick={() => setMode(mode === "signin" ? "signup" : "signin")} className="mt-4 w-full text-center text-sm font-semibold text-primary underline-offset-4 hover:underline">
              {mode === "signin" ? "Need an account? Sign up" : "Already have an account? Sign in"}
            </button>
            {msg ? (
              <motion.p initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="mt-4 text-sm text-error">
                {msg}
              </motion.p>
            ) : null}
            <p className="mt-7 text-center text-sm">
              <Link href="/" className="font-bold text-primary underline-offset-4 hover:underline">
                Back home
              </Link>
            </p>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center px-4 text-sm text-on-surface-variant">Loading sign-in...</div>}>
      <LoginForm />
    </Suspense>
  );
}
