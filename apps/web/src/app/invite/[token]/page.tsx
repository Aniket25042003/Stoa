"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { routeForSessionState, type SessionState } from "@/lib/auth-workflow";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { AuthBrandMark, AuthCard, AuthCardHeader, AuthPageShell } from "@/components/product";

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
          <p className="mt-8 max-w-md font-dm-sans text-sm leading-relaxed text-mkt-muted">
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
        {error ? <p className="font-dm-sans text-sm text-mkt-accent-warm">{error}</p> : null}
        <p className="mt-7 text-center font-dm-sans text-sm">
          <Link href="/dashboard" className="font-semibold text-mkt-accent underline-offset-4 hover:underline">
            Go to dashboard
          </Link>
        </p>
      </AuthCard>
    </AuthPageShell>
  );
}
