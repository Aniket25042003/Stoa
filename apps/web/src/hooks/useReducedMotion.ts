/**
 * @file apps/web/src/hooks/useReducedMotion.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies React
 */
"use client";

import { useEffect, useState } from "react";

/**
 * Handles use reduced motion behavior for this part of the Stoa application.
 * @returns Result consumed by the caller or rendered by React.
 */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const onChange = () => setReduced(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);
  return reduced;
}
