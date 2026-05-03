"use client";

import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/cn";

export function GradientOrb({ className }: { className?: string }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      aria-hidden
      className={cn(
        "pointer-events-none absolute left-1/2 top-[-10%] h-[min(600px,80vw)] w-[min(600px,80vw)] -translate-x-1/2 rounded-full bg-gradient-to-br from-slate/35 via-ink/20 to-transparent blur-3xl",
        className
      )}
      animate={
        reduce
          ? undefined
          : {
              x: ["-5%", "5%", "-3%", "0%"],
              y: ["0%", "4%", "-2%", "0%"],
            }
      }
      transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
    />
  );
}
