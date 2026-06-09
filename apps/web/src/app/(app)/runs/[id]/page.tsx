import Link from "next/link";
import { redirect } from "next/navigation";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { createClient } from "@/lib/supabase/server";
import { RunDetail } from "./ui";

export default async function RunDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect(getAuthEntryPath());

  return (
    <div className="space-y-7">
      <div className="rounded-[2rem] bg-slate-deep p-7 text-white shadow-card md:p-10">
        <Link href="/dashboard" className="font-mono text-xs font-semibold uppercase tracking-[0.12em] text-inverse-primary hover:text-white">
          Back to dashboard
        </Link>
        <h1 className="mt-5 font-display text-4xl font-extrabold tracking-[-0.045em] md:text-5xl">Run {id.slice(0, 8)}...</h1>
      </div>
      <RunDetail runId={id} />
    </div>
  );
}
