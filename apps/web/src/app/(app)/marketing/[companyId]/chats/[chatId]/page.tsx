/**
 * @file apps/web/src/app/(app)/marketing/[companyId]/chats/[chatId]/page.tsx
 * @layer Frontend Product UI
 * @description Defines the route entry point and composes the page-level UI for this product surface.
 * @dependencies Next.js, React
 */
import { redirect } from "next/navigation";

/**
 * Handles legacy marketing chat page behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export default function LegacyMarketingChatPage() {
  redirect("/campaigns");
}
