/**
 * @file apps/web/src/hooks/useDeferredMarketingMedia.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies React
 */
"use client";

import { useEffect, useState } from "react";
import { isMarketingMediaReady, MARKETING_MEDIA_READY_EVENT } from "@/lib/marketing-media";

/** True once LoadingGate has finished (or was skipped on repeat visit). */
export function useDeferredMarketingMedia(): boolean {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (isMarketingMediaReady()) {
      setReady(true);
      return;
    }

    const onReady = () => setReady(true);
    window.addEventListener(MARKETING_MEDIA_READY_EVENT, onReady);
    return () => window.removeEventListener(MARKETING_MEDIA_READY_EVENT, onReady);
  }, []);

  return ready;
}
