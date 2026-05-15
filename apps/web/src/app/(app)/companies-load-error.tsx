import Link from "next/link";

export function CompaniesLoadError({ retryHref }: { retryHref: string }) {
  return (
    <div className="mx-auto max-w-lg space-y-4 px-6 py-16 text-center">
      <h1 className="font-display text-2xl font-bold tracking-[-0.02em] text-on-surface">Could not load companies</h1>
      <p className="text-sm leading-7 text-on-surface-variant">
        The workspace could not reach the companies API. You were not redirected because your session is valid—try again shortly instead of creating a duplicate company.
      </p>
      <Link href={retryHref} className="btn-primary inline-flex justify-center px-6 py-3 text-sm">
        Retry
      </Link>
    </div>
  );
}
