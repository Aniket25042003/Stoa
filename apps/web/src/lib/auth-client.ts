/**
 * @file apps/web/src/lib/auth-client.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
import { getAuthEntryPath } from "@/lib/auth-entry";

type SignOutRouter = {
  push: (href: string) => void;
  refresh: () => void;
};

/**
 * Handles sign out client behavior for this part of the Stoa application.
 *
 * @param router - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
export async function signOutClient(router: SignOutRouter): Promise<boolean> {
  try {
    const res = await fetch("/api/auth/signout", { method: "POST" });
    if (!res.ok) {
      console.error("Sign out failed", res.status);
      return false;
    }
    router.push(getAuthEntryPath());
    router.refresh();
    return true;
  } catch (error) {
    console.error("Sign out failed", error);
    return false;
  }
}
