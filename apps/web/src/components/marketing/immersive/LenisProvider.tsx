/**
 * @file apps/web/src/components/marketing/immersive/LenisProvider.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React
 */
"use client";

import { useEffect } from "react";
import Lenis from "lenis";

/**
 * Handles lenis provider behavior for this part of the Stoa application.
 *
 * @param children - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function LenisProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reducedMotion) return;

    const isMobile = window.innerWidth < 768;

    const lenis = new Lenis({
      duration: isMobile ? 1.1 : 1.4,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: "vertical",
      gestureOrientation: "vertical",
      smoothWheel: true,
      wheelMultiplier: isMobile ? 0.9 : 1.1,
      touchMultiplier: 1.2,
      autoRaf: true,
    });

    const root = document.documentElement;
    root.classList.add("lenis", "lenis-smooth");

    return () => {
      root.classList.remove("lenis", "lenis-smooth", "lenis-stopped", "lenis-scrolling");
      lenis.destroy();
    };
  }, []);

  return <>{children}</>;
}
