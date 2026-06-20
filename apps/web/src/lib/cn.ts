/**
 * @file apps/web/src/lib/cn.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Handles cn behavior for this part of the Stoa application.
 *
 * @param inputs - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
