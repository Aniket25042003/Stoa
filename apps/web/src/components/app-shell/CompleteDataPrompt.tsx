import Link from "next/link";

export function CompleteDataPrompt({
  title,
  message,
  missing,
}: {
  title: string;
  message: string;
  missing?: string[];
}) {
  return (
    <div className="rounded-3xl border border-primary/30 bg-primary/5 p-6 card-glass">
      <h3 className="font-display text-lg font-bold text-on-surface">{title}</h3>
      <p className="mt-2 text-sm leading-7 text-on-surface-variant">{message}</p>
      {missing && missing.length > 0 ? (
        <p className="mt-2 text-xs text-on-surface-variant">
          Missing: {missing.join(", ")}
        </p>
      ) : null}
      <Link href="/data" className="btn-primary mt-4 inline-flex px-4 py-2 text-sm">
        Go to Data hub
      </Link>
    </div>
  );
}
