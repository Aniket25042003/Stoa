/**
 * @file apps/web/src/app/verify-email/page.tsx
 * @layer Application Source
 * @description Defines the route entry point and composes the page-level UI for this product surface.
 * @dependencies Next.js, React
 */
"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { routeForSessionState, safeNextPath, type SessionState } from "@/lib/auth-workflow";
import {
  AuthBrandMark,
  AuthCard,
  AuthCardHeader,
  AuthPageShell,
  ProductButton,
  ProductInput,
} from "@/components/product";

/**
 * Handles verify email client behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
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
      setMessage(body?.detail || "Could not send verification email. Try again shortly.");
    }
  }

  return (
    <AuthPageShell
      lead={
        <div>
          <AuthBrandMark />
          <p className="mt-8 max-w-md font-dm-sans text-sm leading-relaxed text-mkt-muted">
            We need to confirm your email before you can access your workspace. This page refreshes automatically once verification completes.
          </p>
        </div>
      }
    >
      <AuthCard>
        <AuthCardHeader
          eyebrow="Verify email"
          title="Check your inbox"
          description="We sent a confirmation link to your email. Click it to verify your account — you will be signed in automatically."
        />
        <div className="space-y-4">
          <div>
            <label className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.18em] text-mkt-muted">Email</label>
            <ProductInput
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              type="email"
              required
              autoComplete="email"
              placeholder="you@company.com"
              className="mt-1.5"
            />
          </div>
          <ProductButton className="w-full" disabled={resending} onClick={() => void resend()}>
            {resending ? "Sending..." : "Resend verification link"}
          </ProductButton>
          <p className="font-dm-sans text-xs leading-relaxed text-mkt-muted">
            Already clicked the link? This page will redirect you automatically once verification completes.
          </p>
        </div>
        {message ? <p className="mt-4 font-dm-sans text-sm text-mkt-muted">{message}</p> : null}
        <p className="mt-7 text-center font-dm-sans text-sm">
          <Link href={`/login?next=${encodeURIComponent(next)}`} className="font-semibold text-mkt-accent underline-offset-4 hover:underline">
            Back to sign in
          </Link>
        </p>
      </AuthCard>
    </AuthPageShell>
  );
}

/**
 * Handles verify email page behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <div className="product-v2 flex min-h-screen items-center justify-center px-4 font-dm-sans text-sm text-mkt-muted">
          Loading...
        </div>
      }
    >
      <VerifyEmailClient />
    </Suspense>
  );
}
