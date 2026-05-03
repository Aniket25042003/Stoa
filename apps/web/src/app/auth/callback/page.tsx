import { Suspense } from "react";
import { AuthCallbackClient } from "./auth-callback-client";

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center text-sm text-ink/70">Signing you in…</div>
      }
    >
      <AuthCallbackClient />
    </Suspense>
  );
}
