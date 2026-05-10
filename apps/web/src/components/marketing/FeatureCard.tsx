"use client";

import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/cn";
import type { LucideIcon } from "lucide-react";

export function FeatureCard({
  icon: Icon,
  title,
  description,
  className,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  className?: string;
}) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={cn("group relative overflow-hidden rounded-2xl p-8 card-glass", className)}
      whileHover={reduce ? undefined : { y: -6, boxShadow: "var(--shadow-glow)" }}
      transition={{ type: "spring", stiffness: 260, damping: 24 }}
    >
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent" />
      <div className="mb-6 inline-flex rounded-2xl border border-outline-variant/70 bg-surface-container-low/70 p-3 text-primary shadow-soft backdrop-blur-md transition-transform duration-300 group-hover:scale-105">
        <Icon className="h-6 w-6" strokeWidth={1.7} />
      </div>
      <h3 className="font-display text-2xl font-bold tracking-[-0.02em] text-on-surface">{title}</h3>
      <p className="mt-3 text-base leading-7 text-on-surface-variant">{description}</p>
    </motion.div>
  );
}
