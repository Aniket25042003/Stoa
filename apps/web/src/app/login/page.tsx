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
import { SolidButton } from "@/components/marketing/v3/Buttons";
import { DualToneHeadline } from "@/components/marketing/v3/DualToneHeadline";
import { routeForSessionState, safeNextPath, loginErrorMessage, type SessionState } from "@/lib/auth-workflow";
import { BRAND_NAME, BRAND_SUBHEAD } from "@/lib/brand";
import {
  AuthBrandMark,
  AuthCard,
  AuthCardHeader,
  AuthDivider,
  AuthInput,
  AuthLabel,
  AuthOutlineButton,
  AuthPageShell,
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
    if (err) setMsg(loginErrorMessage(err));
  }, [searchParams]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const res = await fetch("/api/auth/session", { cache: "no-store" });
      if (!res.ok || cancelled) return;
      const state = (await res.json()) as SessionState & { authenticated?: boolean };
      if (state.authenticated) {
        window.location.replace(routeForSessionState(state, next));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [next]);

  async function postAuthRoute() {
    const res = await fetch("/api/auth/session");
    if (!res.ok) return next;
    const state = (await res.json()) as SessionState & { authenticated?: boolean };
    if (!state.authenticated) return next;
    return routeForSessionState(state, next);
  }

  async function signInWithGoogle() {
    setMsg(null);
    setLoading(true);
    const res = await fetch("/api/auth/oauth", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider: "google", next }),
    });
    const body = (await res.json().catch(() => null)) as { url?: string; detail?: string } | null;
    if (!res.ok || !body?.url) {
      setLoading(false);
      setMsg(body?.detail || "Could not start Google sign-in. Try again.");
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
            <DualToneHeadline primary="Know your market." secondary="Ship faster." as="h1" />
            <p className="mt-5 text-base leading-relaxed text-mkt-muted md:text-lg">{BRAND_SUBHEAD}</p>
            <p className="mt-4 text-sm leading-relaxed text-mkt-muted">
              Sign in with Google or your work email to open your {BRAND_NAME} workspace.
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
            description="Use Google SSO or email/password. Email accounts verify through your inbox before first sign-in."
          />
          <AuthOutlineButton disabled={loading} onClick={() => void signInWithGoogle()}>
            <GoogleIcon className="h-5 w-5 shrink-0" />
            {loading ? "Redirecting..." : "Continue with Google"}
          </AuthOutlineButton>
          <AuthDivider label="Work email" />
          <form onSubmit={(event) => void submitEmail(event)} className="space-y-4">
            {mode === "signup" ? (
              <div className="space-y-1.5">
                <AuthLabel htmlFor="full_name">Full name</AuthLabel>
                <AuthInput id="full_name" name="full_name" type="text" required autoComplete="name" placeholder="Jane Doe" />
              </div>
            ) : null}
            <div className="space-y-1.5">
              <AuthLabel htmlFor="email">Email</AuthLabel>
              <AuthInput id="email" name="email" type="email" required placeholder="you@company.com" />
            </div>
            <div className="space-y-1.5">
              <AuthLabel htmlFor="password">Password</AuthLabel>
              <AuthInput
                id="password"
                name="password"
                type="password"
                required
                minLength={8}
                placeholder="At least 8 characters"
              />
            </div>
            <SolidButton type="submit" disabled={loading} variant="dark" className="w-full justify-center py-3">
              {loading ? "Working..." : mode === "signin" ? "Sign in with email" : "Create account"}
            </SolidButton>
          </form>
          <button
            type="button"
            onClick={() => setMode(mode === "signin" ? "signup" : "signin")}
            className="mt-4 w-full text-center text-sm font-medium text-mkt-ink underline-offset-4 hover:underline"
          >
            {mode === "signin" ? "Need an account? Sign up" : "Already have an account? Sign in"}
          </button>
          {msg ? (
            <motion.p
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm leading-relaxed text-red-700"
            >
              {msg}
            </motion.p>
          ) : null}
          <p className="mt-7 text-center text-sm text-mkt-muted">
            <Link href="/" className="font-medium text-mkt-ink underline-offset-4 hover:underline">
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
        <div className="product-v2 flex min-h-screen items-center justify-center px-4 text-sm text-mkt-muted">
          Loading sign-in...
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
