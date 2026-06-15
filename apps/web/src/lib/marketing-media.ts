/** Fired by LoadingGate when the intro completes (or was skipped). */
export const MARKETING_MEDIA_READY_EVENT = "stoa-media-ready";

export function isMarketingMediaReady(): boolean {
  if (typeof window === "undefined") return false;
  return sessionStorage.getItem("stoa_gate_seen") === "true";
}

export function notifyMarketingMediaReady(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(MARKETING_MEDIA_READY_EVENT));
}
