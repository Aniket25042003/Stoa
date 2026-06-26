/**
 * @file apps/web/src/app/(app)/marketing/page.tsx
 * @layer Frontend Product UI
 * @description Defines the route entry point and composes the page-level UI for this product surface.
 * @dependencies Next.js, React
 */
import { redirect } from "next/navigation";

/**
 * Handles marketing redirect page behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export default function MarketingRedirectPage() {
  redirect("/assets?type=campaigns");
}
