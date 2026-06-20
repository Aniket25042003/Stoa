/**
 * @file apps/web/src/lib/host.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
export function resolveHostname(hostname?: string): string | undefined {
  if (hostname) return hostname;
  if (typeof window !== "undefined") return window.location.hostname;
  return undefined;
}

/**
 * Handles is loopback host behavior for this part of the Stoa application.
 *
 * @param hostname - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
export function isLoopbackHost(hostname: string | undefined): boolean {
  if (!hostname) return false;
  const host = hostname.toLowerCase();
  return host === "localhost" || host === "127.0.0.1" || host === "[::1]";
}
