/**
 * @file apps/web/src/components/motion/StaggerInView.tsx
 * @layer Application Source
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React, Framer Motion
 */
"use client";

import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/cn";
import type { ReactNode } from "react";

/**
 * Handles stagger in view behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function StaggerInView({
  children,
  className,
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={cn(className)}
      initial={reduce ? false : { opacity: 0, y: 20 }}
      whileInView={reduce ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.4, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}
