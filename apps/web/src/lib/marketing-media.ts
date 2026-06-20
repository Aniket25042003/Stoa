/**
 * @file apps/web/src/lib/marketing-media.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
/** Fired by LoadingGate when the intro completes (or was skipped). */
export const MARKETING_MEDIA_READY_EVENT = "stoa-media-ready";

/**
 * Handles is marketing media ready behavior for this part of the Stoa application.
 * @returns Result consumed by the caller or rendered by React.
 */
export function isMarketingMediaReady(): boolean {
  if (typeof window === "undefined") return false;
  return sessionStorage.getItem("stoa_gate_seen") === "true";
}

/**
 * Handles notify marketing media ready behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function notifyMarketingMediaReady(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(MARKETING_MEDIA_READY_EVENT));
}
