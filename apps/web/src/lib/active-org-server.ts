/**
 * @file apps/web/src/lib/active-org-server.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies Next.js
 */
import { cookies } from "next/headers";
import { ACTIVE_ORG_COOKIE } from "@/lib/active-org";

/**
 * Handles get server active org id behavior for this part of the Stoa application.
 * @returns Result consumed by the caller or rendered by React.
 */
export async function getServerActiveOrgId(): Promise<string | null> {
  const jar = await cookies();
  return jar.get(ACTIVE_ORG_COOKIE)?.value ?? null;
}
