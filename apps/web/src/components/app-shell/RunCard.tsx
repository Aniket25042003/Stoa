import Link from "next/link";
import { StatusPill } from "./StatusPill";

export function RunCard({ id, status, createdAt }: { id: string; status: string; createdAt: string }) {
  return (
    <Link href={`/runs/${id}`} className="group relative overflow-hidden rounded-3xl p-5 transition-transform hover:-translate-y-1 card-glass">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/45 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-mono text-sm font-semibold text-slate-deep">{id.slice(0, 8)}...</span>
        <StatusPill status={status} />
      </div>
      <p className="mt-3 text-xs text-on-surface-variant">{createdAt}</p>
      <span className="mt-5 inline-flex text-sm font-bold text-primary underline-offset-4 group-hover:underline">View run</span>
    </Link>
  );
}
