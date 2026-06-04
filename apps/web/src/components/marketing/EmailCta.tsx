import Link from "next/link";

export function EmailCta() {
  return (
    <Link href="/waitlist" className="btn-primary shrink-0 px-6 py-3 text-center text-sm font-mono uppercase tracking-wider">
      JOIN_WAITLIST.SH
    </Link>
  );
}
