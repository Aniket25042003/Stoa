import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { apiFetch } from "@/lib/api";
import { NewCompanyForm } from "./new-company-form";

type Company = { id: string; name: string; created_at: string };

export default async function MarketingPage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) redirect("/login");

  let companies: Company[] = [];
  try {
    const res = await apiFetch("/v1/companies", { accessToken: session.access_token });
    if (res.ok) {
      const body = await res.json();
      companies = body.companies ?? [];
    }
  } catch {
    companies = [];
  }

  return (
    <div className="space-y-8">
      <div className="rounded-[2rem] bg-slate-deep p-7 text-white shadow-card md:p-10">
        <Link href="/dashboard" className="font-mono text-xs font-semibold uppercase tracking-[0.12em] text-inverse-primary hover:text-white">
          Back to dashboard
        </Link>
        <h1 className="mt-5 font-display text-4xl font-extrabold tracking-[-0.045em] md:text-5xl">Marketing workspaces</h1>
        <p className="mt-4 max-w-2xl text-sm text-white/70">
          Each workspace shares one knowledge base with your GTM runs—competitors, positioning, and learnings compound across agents.
        </p>
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          {companies.length === 0 ? (
            <p className="text-on-surface-variant">No workspaces yet. Create one on the right.</p>
          ) : (
            <ul className="space-y-3">
              {companies.map((c) => (
                <li key={c.id}>
                  <Link
                    href={`/marketing/${c.id}`}
                    className="block rounded-2xl border border-outline-variant/50 bg-surface-container-low/80 px-5 py-4 transition hover:border-primary/40"
                  >
                    <span className="font-semibold text-on-surface">{c.name}</span>
                    <span className="mt-1 block font-mono text-xs text-on-surface-variant">{c.id}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
        <NewCompanyForm accessToken={session.access_token} />
      </div>
    </div>
  );
}
