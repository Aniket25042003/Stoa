import { Suspense } from "react";
import { AuthCallbackClient } from "./auth-callback-client";

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center text-sm text-on-surface-variant">Signing you in...</div>}>
      <AuthCallbackClient />
    </Suspense>
  );
}
