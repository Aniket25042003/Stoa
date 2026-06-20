/**
 * @file apps/web/src/app/login/page.tsx
 * @layer Application Source
 * @description Defines the route entry point and composes the page-level UI for this product surface.
 * @dependencies Next.js, React, Framer Motion
 */
"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { routeForSessionState, safeNextPath, type SessionState } from "@/lib/auth-workflow";
import { BRAND_NAME, BRAND_SUBHEAD, BRAND_TAGLINE } from "@/lib/brand";
import {
  AuthBrandMark,
  AuthCard,
  AuthCardHeader,
  AuthPageShell,
  ProductButton,
  ProductInput,
} from "@/components/product";

/**
 * Handles google icon behavior for this part of the Stoa application.
 *
 * @param className - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
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

const labelClass = "font-dm-sans text-[9px] font-bold uppercase tracking-[0.18em] text-mkt-muted";

/**
 * Handles login form behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
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
        if (!res.ok) throw new Error(body?.detail || "Could not create account. Try again.");
        if (body?.status === "created_email_pending" && body.detail) setMsg(body.detail);
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
    <AuthPageShell
      lead={
        <>
          <AuthBrandMark />
          <div className="mt-8">
            <p className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.22em] text-mkt-accent">
              Secure workspace
            </p>
            <h1 className="mt-4 font-syne text-4xl font-extrabold uppercase leading-tight tracking-tight text-mkt-ink md:text-5xl">
              {BRAND_TAGLINE}
            </h1>
            <p className="mt-5 font-dm-sans text-base leading-relaxed text-mkt-muted">{BRAND_SUBHEAD}</p>
            <p className="mt-4 font-dm-sans text-sm leading-relaxed text-mkt-muted">
              Sign in with Google, Microsoft, or your work email to open your {BRAND_NAME} workspace.
            </p>
          </div>
        </>
      }
    >
      <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
        <AuthCard>
          <AuthCardHeader
            eyebrow="Authentication"
            title="Continue to dashboard"
            description="Use SSO or email/password. Email accounts verify through your inbox before first sign-in."
          />
          <ProductButton
            variant="secondary"
            className="w-full"
            disabled={loading}
            onClick={() => void signInWithProvider("google")}
          >
            <GoogleIcon className="h-5 w-5 shrink-0" />
            {loading ? "Redirecting..." : "Continue with Google"}
          </ProductButton>
          <ProductButton
            variant="secondary"
            className="mt-3 w-full"
            disabled={loading}
            onClick={() => void signInWithProvider("azure")}
          >
            <span className="grid h-5 w-5 shrink-0 grid-cols-2 gap-0.5" aria-hidden>
              <span className="bg-[#f25022]" />
              <span className="bg-[#7fba00]" />
              <span className="bg-[#00a4ef]" />
              <span className="bg-[#ffb900]" />
            </span>
            {loading ? "Redirecting..." : "Continue with Microsoft"}
          </ProductButton>
          <div className="my-6 flex items-center gap-3 font-dm-sans text-[9px] font-bold uppercase tracking-[0.16em] text-mkt-muted">
            <span className="h-px flex-1 bg-mkt-ink/10" />
            Work email
            <span className="h-px flex-1 bg-mkt-ink/10" />
          </div>
          <form onSubmit={(event) => void submitEmail(event)} className="space-y-4">
            {mode === "signup" ? (
              <div>
                <label className={labelClass}>Full name</label>
                <ProductInput name="full_name" type="text" required autoComplete="name" placeholder="Jane Doe" className="mt-1.5" />
              </div>
            ) : null}
            <div>
              <label className={labelClass}>Email</label>
              <ProductInput name="email" type="email" required placeholder="you@company.com" className="mt-1.5" />
            </div>
            <div>
              <label className={labelClass}>Password</label>
              <ProductInput name="password" type="password" required minLength={8} placeholder="At least 8 characters" className="mt-1.5" />
            </div>
            <ProductButton type="submit" className="w-full" disabled={loading}>
              {loading ? "Working..." : mode === "signin" ? "Sign in with email" : "Create account"}
            </ProductButton>
          </form>
          <button
            type="button"
            onClick={() => setMode(mode === "signin" ? "signup" : "signin")}
            className="mt-4 w-full text-center font-dm-sans text-sm font-semibold text-mkt-accent underline-offset-4 hover:underline"
          >
            {mode === "signin" ? "Need an account? Sign up" : "Already have an account? Sign in"}
          </button>
          {msg ? (
            <motion.p initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="mt-4 font-dm-sans text-sm text-mkt-accent-warm">
              {msg}
            </motion.p>
          ) : null}
          <p className="mt-7 text-center font-dm-sans text-sm">
            <Link href="/" className="font-semibold text-mkt-accent underline-offset-4 hover:underline">
              Back home
            </Link>
          </p>
        </AuthCard>
      </motion.div>
    </AuthPageShell>
  );
}

/**
 * Handles login page behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="product-v2 flex min-h-screen items-center justify-center px-4 font-dm-sans text-sm text-mkt-muted">
          Loading sign-in...
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
