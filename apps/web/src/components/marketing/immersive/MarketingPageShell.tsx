/**
 * @file apps/web/src/components/marketing/immersive/MarketingPageShell.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React
 */
"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

/**
 * Handles marketing page shell behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function MarketingPageShell({
  children,
  className,
  contentClassName,
}: {
  children: ReactNode;
  className?: string;
  contentClassName?: string;
}) {
  return (
    <div className={cn("relative bg-mkt-surface", className)}>
      <div className="pointer-events-none absolute inset-0" aria-hidden>
        <div className="absolute -right-[10%] top-0 h-[min(420px,45vh)] w-[min(420px,45vh)] rounded-full bg-mkt-accent/[0.06] blur-3xl" />
        <div className="absolute -left-[8%] bottom-[20%] h-[min(320px,35vh)] w-[min(320px,35vh)] rounded-full bg-mkt-accent-warm/[0.05] blur-3xl" />
        <div
          className="absolute inset-0 opacity-[0.28]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(20,20,26,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(20,20,26,0.035) 1px, transparent 1px)",
            backgroundSize: "48px 48px",
            maskImage: "radial-gradient(ellipse 90% 60% at 50% 0%, black 15%, transparent 70%)",
          }}
        />
      </div>

      <div
        className={cn(
          "relative z-10 mx-auto max-w-7xl px-4 py-16 md:px-8 md:py-24",
          contentClassName
        )}
      >
        {children}
      </div>
    </div>
  );
}
