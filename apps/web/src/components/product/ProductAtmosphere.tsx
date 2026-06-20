/**
 * @file apps/web/src/components/product/ProductAtmosphere.tsx
 * @layer Frontend Design System
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React
 */
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

/** Calmer workspace atmosphere — same motifs as marketing, lower intensity. */
export function ProductAtmosphere({ className }: { className?: string }) {
  return (
    <div className={cn("pointer-events-none fixed inset-0 -z-10", className)} aria-hidden>
      <div className="absolute -right-[12%] top-0 h-[min(360px,40vh)] w-[min(360px,40vh)] rounded-full bg-mkt-accent/[0.04] blur-3xl" />
      <div className="absolute -left-[10%] bottom-[10%] h-[min(280px,32vh)] w-[min(280px,32vh)] rounded-full bg-mkt-accent-warm/[0.03] blur-3xl" />
      <div
        className="absolute inset-0 opacity-[0.18]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(20,20,26,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(20,20,26,0.03) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
          maskImage: "radial-gradient(ellipse 100% 80% at 50% 0%, black 10%, transparent 75%)",
        }}
      />
    </div>
  );
}

/**
 * Handles product shell frame behavior for this part of the Stoa application.
 *
 * @param children - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ProductShellFrame({ children }: { children: ReactNode }) {
  return (
    <div className="product-v2 relative min-h-screen text-mkt-ink">
      <ProductAtmosphere />
      {children}
    </div>
  );
}
