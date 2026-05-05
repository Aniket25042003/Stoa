import Link from "next/link";

export function EmailCta() {
  return (
    <Link href="/login" className="btn-primary shrink-0 px-6 py-3 text-center text-sm">
      Sign in with Google
    </Link>
  );
}
