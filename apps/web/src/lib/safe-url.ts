/**
 * @file apps/web/src/lib/safe-url.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
export function isSafeExternalHref(url: string): boolean {
  try {
    const parsed = new URL(url.trim());
    return (parsed.protocol === "http:" || parsed.protocol === "https:") && Boolean(parsed.hostname);
  } catch {
    return false;
  }
}

/**
 * Handles safe external href behavior for this part of the Stoa application.
 *
 * @param url - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
export function safeExternalHref(url: string): string | undefined {
  return isSafeExternalHref(url) ? url : undefined;
}
