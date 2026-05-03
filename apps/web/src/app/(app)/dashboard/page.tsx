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
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-ink md:text-4xl">Your GTM runs</h1>
          <p className="mt-2 text-sm text-ink/65">Signed in as {session.user.email}</p>
        </div>
        <Link
          href="/runs/new"
          className="inline-flex items-center justify-center rounded-lg bg-slate px-5 py-2.5 text-sm font-semibold text-cream shadow-glow transition-opacity hover:opacity-90"
        >
          New run
        </Link>
      </div>

      {runs.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-mist bg-cream/80 px-6 py-16 text-center">
          <p className="text-lg font-medium text-ink">No runs yet</p>
          <p className="mt-2 text-sm text-ink/65">Create a master plan when your API and Supabase session are configured.</p>
          <Link
            href="/runs/new"
            className="mt-6 inline-flex rounded-lg bg-slate px-5 py-2.5 text-sm font-semibold text-cream shadow-glow transition-opacity hover:opacity-90"
          >
            Create your first run
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {runs.map((r) => (
            <RunCard key={r.id} id={r.id} status={r.status} createdAt={r.created_at} />
          ))}
        </div>
      )}
    </div>
  );
}
