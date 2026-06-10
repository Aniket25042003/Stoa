import Link from "next/link";
import { getAuthEntryPath } from "@/lib/auth-entry";

const authEntry = getAuthEntryPath();

export function EmailCta() {
  return (
    <Link href={authEntry} className="btn-primary shrink-0 px-6 py-3 text-center text-sm font-mono uppercase tracking-wider">
      JOIN_WAITLIST.SH
    </Link>
  );
}
