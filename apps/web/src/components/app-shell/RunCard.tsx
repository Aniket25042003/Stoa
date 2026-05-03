import Link from "next/link";
import { StatusPill } from "./StatusPill";

export function RunCard({ id, status, createdAt }: { id: string; status: string; createdAt: string }) {
  return (
    <Link
      href={`/runs/${id}`}
      className="group flex flex-col gap-3 rounded-2xl border border-mist bg-cream/95 p-5 transition-[box-shadow,transform] hover:-translate-y-0.5 hover:shadow-glow"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-mono text-sm text-ink">{id.slice(0, 8)}…</span>
        <StatusPill status={status} />
      </div>
      <p className="text-xs text-ink/60">{createdAt}</p>
      <span className="text-sm font-medium text-slate group-hover:underline">View run →</span>
    </Link>
  );
}
