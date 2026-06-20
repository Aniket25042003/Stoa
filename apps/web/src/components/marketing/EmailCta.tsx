/**
 * @file apps/web/src/components/marketing/EmailCta.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies Next.js, React
 */
import Link from "next/link";
import { getAuthEntryPath } from "@/lib/auth-entry";

const authEntry = getAuthEntryPath();

/**
 * Handles email cta behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function EmailCta() {
  return (
    <Link href={authEntry} className="btn-primary shrink-0 px-6 py-3 text-center text-sm font-mono uppercase tracking-wider">
      JOIN_WAITLIST.SH
    </Link>
  );
}
