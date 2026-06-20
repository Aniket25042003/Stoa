/**
 * @file apps/web/src/app/(marketing)/how-it-works/page.tsx
 * @layer Frontend Marketing UI
 * @description Defines the route entry point and composes the page-level UI for this product surface.
 * @dependencies Next.js, React
 */
import { redirect } from "next/navigation";

/**
 * Handles how it works redirect behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export default function HowItWorksRedirect() {
  redirect("/see-it-in-action");
}
