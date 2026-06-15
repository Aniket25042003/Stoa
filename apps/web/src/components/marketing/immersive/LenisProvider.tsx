"use client";

import { useEffect } from "react";
import Lenis from "lenis";

export function LenisProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    if (window.innerWidth < 768) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reducedMotion) return;

    const lenis = new Lenis({
      duration: 1.4,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: "vertical",
      gestureOrientation: "vertical",
      smoothWheel: true,
      wheelMultiplier: 1.1,
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
