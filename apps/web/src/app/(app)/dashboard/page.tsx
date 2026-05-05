import Link from "next/link";
import { redirect } from "next/navigation";
import { RunCard } from "@/components/app-shell/RunCard";
import { createClient } from "@/lib/supabase/server";
import { apiFetch } from "@/lib/api";

export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) redirect("/login");

  let runs: { id: string; status: string; created_at: string }[] = [];
  try {
    const res = await apiFetch("/v1/runs", { accessToken: session.access_token });
    if (res.ok) {
      const body = await res.json();
      runs = body.runs ?? [];
    }
  } catch {
    runs = [];
  }

  return (
    <div className="space-y-10">
      <div className="rounded-[2rem] bg-slate-deep p-7 text-white shadow-card md:p-10">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="eyebrow text-inverse-primary">Workspace</p>
            <h1 className="mt-4 font-display text-4xl font-extrabold tracking-[-0.045em] md:text-5xl">Your GTM runs</h1>
            <p className="mt-3 text-sm text-white/62">Signed in as {session.user.email}</p>
          </div>
          <Link href="/runs/new" className="btn-primary px-5 py-3 text-sm">
            New run
          </Link>
        </div>
      </div>

      {runs.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-primary/28 bg-white/64 px-6 py-16 text-center shadow-soft backdrop-blur-md">
          <p className="font-display text-2xl font-bold text-slate-deep">No runs yet</p>
          <p className="mt-3 text-sm text-on-surface-variant">Create a master plan when your API and Supabase session are configured.</p>
          <Link href="/runs/new" className="btn-primary mt-7 px-5 py-3 text-sm">
            Create your first run
          </Link>
        </div>
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {runs.map((r) => (
            <RunCard key={r.id} id={r.id} status={r.status} createdAt={r.created_at} />
          ))}
        </div>
      )}
    </div>
  );
}
