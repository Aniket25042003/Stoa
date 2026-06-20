/**
 * @file apps/web/src/components/marketing/MagneticButton.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React, Framer Motion
 */
"use client";

import { motion, useMotionTemplate, useMotionValue, useSpring, useReducedMotion } from "framer-motion";
import type { ComponentProps, ReactNode } from "react";
import { cn } from "@/lib/cn";

type MotionButtonProps = ComponentProps<typeof motion.button>;

/**
 * Handles magnetic button behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function MagneticButton({
  children,
  className,
  variant = "primary",
  type = "button",
  ...props
}: MotionButtonProps & { variant?: "primary" | "outline"; children: ReactNode }) {
  const reduce = useReducedMotion();
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const sx = useSpring(x, { stiffness: 200, damping: 20 });
  const sy = useSpring(y, { stiffness: 200, damping: 20 });
  const transform = useMotionTemplate`translate(${sx}px, ${sy}px)`;

  return (
    <motion.button
      type={type}
      className={cn(
        "px-5 py-2.5 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary",
        variant === "primary" ? "btn-primary" : "btn-secondary",
        className
      )}
      style={reduce ? undefined : { transform }}
      onMouseMove={(e) => {
        if (reduce) return;
        const rect = e.currentTarget.getBoundingClientRect();
        const dx = e.clientX - (rect.left + rect.width / 2);
        const dy = e.clientY - (rect.top + rect.height / 2);
        x.set(dx * 0.08);
        y.set(dy * 0.08);
      }}
      onMouseLeave={() => {
        x.set(0);
        y.set(0);
      }}
      {...props}
    >
      {children}
    </motion.button>
  );
}
