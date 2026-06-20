/**
 * @file apps/web/src/components/marketing/immersive/ScrollProgress.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React
 */
"use client";

import { useEffect, useState } from "react";

/**
 * Handles scroll progress behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ScrollProgress() {
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      if (docHeight <= 0) {
        setScrollProgress(0);
        return;
      }
      const progress = (window.scrollY / docHeight) * 100;
      setScrollProgress(progress);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <div className="fixed left-0 right-0 top-0 z-[100] h-[3px] w-full bg-transparent" aria-hidden="true">
      <div
        className="h-full bg-gradient-to-r from-[#4F46E5] to-[#E85D4C] transition-all duration-75 ease-out"
        style={{ width: `${scrollProgress}%` }}
      />
    </div>
  );
}
