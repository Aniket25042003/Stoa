"use client";

import { motion, useMotionTemplate, useMotionValue, useSpring, useReducedMotion } from "framer-motion";
import type { ComponentProps, ReactNode } from "react";
import { cn } from "@/lib/cn";

type MotionButtonProps = ComponentProps<typeof motion.button>;

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

  const base =
    "relative inline-flex items-center justify-center rounded-lg px-5 py-2.5 text-sm font-semibold transition-shadow focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate";
  const styles =
    variant === "primary"
      ? "bg-slate text-cream shadow-glow hover:shadow-[0_24px_64px_-20px_rgb(109_129_150_/_45%)]"
      : "border border-mist bg-cream/80 text-ink hover:border-slate/60";

  return (
    <motion.button
      type={type}
      className={cn(base, styles, className)}
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
