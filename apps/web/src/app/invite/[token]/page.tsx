/**
 * @file apps/web/src/app/invite/[token]/page.tsx
 * @layer Application Source
 * @description Defines the route entry point and composes the page-level UI for this product surface.
 * @dependencies Next.js, React, BFF apiFetch
 */
"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { routeForSessionState, type SessionState } from "@/lib/auth-workflow";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { AuthBrandMark, AuthCard, AuthCardHeader, AuthPageShell } from "@/components/product";

/**
 * Handles invite page behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
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
    <AuthPageShell
      lead={
        <div>
          <AuthBrandMark />
          <p className="mt-8 max-w-md text-sm leading-relaxed text-mkt-muted">
            Accepting your team invite and linking you to the inviting organization.
          </p>
        </div>
      }
    >
      <AuthCard>
        <AuthCardHeader
          eyebrow="Team invite"
          title={message}
          description="You will be linked to the inviting organization after sign-in and verification."
        />
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        <p className="mt-7 text-center text-sm text-mkt-muted">
          <Link href="/dashboard" className="font-medium text-mkt-ink underline-offset-4 hover:underline">
            Go to dashboard
          </Link>
        </p>
      </AuthCard>
    </AuthPageShell>
  );
}
