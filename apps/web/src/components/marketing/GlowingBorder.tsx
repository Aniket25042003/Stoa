"use client";

import { cn } from "@/lib/cn";
import React from "react";

export function GlowingBorder({
  children,
  className,
  containerClassName,
}: {
  children: React.ReactNode;
  className?: string;
  containerClassName?: string;
}) {
  return (
    <div className={cn("relative p-[1px] overflow-hidden rounded-[1.25rem]", containerClassName)}>
      <div className="absolute inset-0 bg-gradient-to-r from-primary via-tertiary to-secondary animate-aurora [background-size:400%_400%]" />
      <div className={cn("relative bg-surface rounded-[calc(1.25rem-1px)] dark:bg-surface-container", className)}>
        {children}
      </div>
    </div>
  );
}
