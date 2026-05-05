"use client";

import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/cn";

export function GradientOrb({ className }: { className?: string }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      aria-hidden
      className={cn(
        "pointer-events-none absolute left-1/2 top-[-18%] h-[min(760px,92vw)] w-[min(760px,92vw)] -translate-x-1/2 rounded-full bg-[radial-gradient(circle_at_32%_30%,rgb(99_102_241_/_0.28),transparent_34%),radial-gradient(circle_at_66%_40%,rgb(139_92_246_/_0.22),transparent_36%),radial-gradient(circle_at_50%_55%,rgb(255_255_255_/_0.9),transparent_48%)] blur-3xl",
        className
      )}
      animate={
        reduce
          ? undefined
          : {
              x: ["-4%", "4%", "-2%", "0%"],
              y: ["0%", "5%", "-2%", "0%"],
              scale: [1, 1.04, 0.98, 1],
            }
      }
      transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
    />
  );
}
