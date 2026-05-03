import { cn } from "@/lib/cn";

export function GridBackground({ className }: { className?: string }) {
  return <div aria-hidden className={cn("pointer-events-none fixed inset-0 -z-10 grid-bg", className)} />;
}
