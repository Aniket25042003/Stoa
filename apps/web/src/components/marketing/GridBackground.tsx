/**
 * @file apps/web/src/components/marketing/GridBackground.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React
 */
import { cn } from "@/lib/cn";

/**
 * Handles grid background behavior for this part of the Stoa application.
 *
 * @param className - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function GridBackground({ className }: { className?: string }) {
  return <div aria-hidden className={cn("pointer-events-none fixed inset-0 -z-10 grid-bg dark:starfield", className)} />;
}
