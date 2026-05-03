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
      className={cn(
        "rounded-2xl border border-mist/80 bg-cream/90 p-8 shadow-sm transition-shadow",
        className
      )}
      whileHover={reduce ? undefined : { y: -4, boxShadow: "var(--shadow-glow)" }}
      transition={{ type: "spring", stiffness: 260, damping: 22 }}
    >
      <div className="mb-4 inline-flex rounded-xl border border-mist bg-cream p-3 text-slate">
        <Icon className="h-6 w-6" strokeWidth={1.5} />
      </div>
      <h3 className="text-2xl font-medium tracking-tight text-ink">{title}</h3>
      <p className="mt-2 text-base leading-7 text-ink/75">{description}</p>
    </motion.div>
  );
}
