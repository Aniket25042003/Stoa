"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { routeForSessionState, type SessionState } from "@/lib/auth-workflow";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { BRAND_NAME } from "@/lib/brand";

export default function InvitePage() {
  const params = useParams<{ token: string }>();
  const router = useRouter();
  const [message, setMessage] = useState("Checking your invite...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      const token = params.token;
      const stateRes = await fetch("/api/auth/session");
      if (!stateRes.ok) {
        router.replace(`${getAuthEntryPath()}?next=${encodeURIComponent(`/invite/${token}`)}`);
        return;
      }
      const state = (await stateRes.json()) as SessionState & { authenticated?: boolean };
      if (!state.authenticated) {
        router.replace(`${getAuthEntryPath()}?next=${encodeURIComponent(`/invite/${token}`)}`);
        return;
      }
      if (state.needs_email_verification) {
        router.replace(`/verify-email?next=${encodeURIComponent(`/invite/${token}`)}`);
        return;
      }

      const res = await apiFetch("/v1/team/invites/accept", {
        method: "POST",
        body: JSON.stringify({ token }),
      });
      const body = await res.json().catch(() => null);
      if (!res.ok) {
        setError(body?.detail || "Could not accept invite.");
        setMessage("Invite could not be accepted.");
        return;
      }

      const nextStateRes = await apiFetch("/v1/auth/session-state");
      if (nextStateRes.ok) {
        const nextState = (await nextStateRes.json()) as SessionState;
        router.replace(routeForSessionState(nextState, "/dashboard"));
        return;
      }
      router.replace("/dashboard");
    })();
  }, [params.token, router]);

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
            <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-inverse-primary">Team invite</p>
            <h1 className="mt-2 font-display text-2xl font-bold tracking-[-0.03em]">{message}</h1>
            <p className="mt-2 text-sm leading-6 text-white/68">You will be linked to the inviting company after sign-in and verification.</p>
          </div>
          {error ? <p className="mt-5 text-sm text-error">{error}</p> : null}
        </div>
      </div>
    </div>
  );
}
