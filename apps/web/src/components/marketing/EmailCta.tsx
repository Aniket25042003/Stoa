import Link from "next/link";

export function EmailCta() {
  return (
    <Link
      href="/login"
      className="inline-flex shrink-0 items-center justify-center rounded-lg bg-cream px-6 py-3 text-center text-sm font-semibold text-ink shadow-sm transition-opacity hover:opacity-90"
    >
      Sign in with Google
    </Link>
  );
}
