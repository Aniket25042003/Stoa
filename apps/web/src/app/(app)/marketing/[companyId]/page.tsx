import Link from "next/link";
import { redirect } from "next/navigation";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { createClient } from "@/lib/supabase/server";
import { apiFetch } from "@/lib/api";
import { NewMarketingChatButton } from "./new-chat-button";

export default async function CompanyMarketingPage({ params }: { params: Promise<{ companyId: string }> }) {
  const { companyId } = await params;
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect(getAuthEntryPath());
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) redirect(getAuthEntryPath());

  let company: { name: string } | null = null;
  let chats: { id: string; title: string; created_at: string }[] = [];
  let runs: { id: string; status: string }[] = [];
  let knowledge: { kind: string; title: string }[] = [];
  try {
    const [co, ch, gtm, kn] = await Promise.all([
      apiFetch(`/v1/companies/${companyId}`, { accessToken: session.access_token }),
      apiFetch(`/v1/companies/${companyId}/chats`, { accessToken: session.access_token }),
      apiFetch(`/v1/companies/${companyId}/gtm-runs`, { accessToken: session.access_token }),
      apiFetch(`/v1/companies/${companyId}/knowledge?limit=12`, { accessToken: session.access_token }),
    ]);
    if (co.ok) {
      const b = await co.json();
      company = b.company ?? null;
    }
    if (ch.ok) {
      const b = await ch.json();
      chats = b.chats ?? [];
    }
    if (gtm.ok) {
      const b = await gtm.json();
      runs = b.runs ?? [];
    }
    if (kn.ok) {
      const b = await kn.json();
      knowledge = b.items ?? [];
    }
  } catch {
    /* empty */
  }

  if (!company) {
    redirect("/marketing");
  }

  return (
    <div className="space-y-8">
      <div className="rounded-[2rem] bg-slate-deep p-7 text-white shadow-card md:p-10">
        <Link href="/marketing" className="font-mono text-xs font-semibold uppercase tracking-[0.12em] text-inverse-primary hover:text-white">
          All workspaces
        </Link>
        <h1 className="mt-5 font-display text-4xl font-extrabold tracking-[-0.045em] md:text-5xl">{company.name}</h1>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href={`/runs/new?company_id=${companyId}`} className="btn-primary px-4 py-2 text-sm">
            New GTM run (linked)
          </Link>
          <NewMarketingChatButton companyId={companyId} />
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-2">
        <section className="rounded-3xl border border-outline-variant/50 bg-surface-container-low/80 p-6">
          <h2 className="font-display text-xl font-bold text-on-surface">Chats</h2>
          <ul className="mt-4 space-y-2">
            {chats.map((c) => (
              <li key={c.id}>
                <Link href={`/marketing/${companyId}/chats/${c.id}`} className="text-primary hover:underline">
                  {c.title}
                </Link>
                <span className="ml-2 font-mono text-xs text-on-surface-variant">{c.id.slice(0, 8)}…</span>
              </li>
            ))}
          </ul>
        </section>
        <section className="rounded-3xl border border-outline-variant/50 bg-surface-container-low/80 p-6">
          <h2 className="font-display text-xl font-bold text-on-surface">GTM runs</h2>
          <ul className="mt-4 space-y-2">
            {runs.map((r) => (
              <li key={r.id}>
                <Link href={`/runs/${r.id}`} className="text-primary hover:underline">
                  {r.id.slice(0, 8)}…
                </Link>
                <span className="ml-2 text-sm text-on-surface-variant">{r.status}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section className="rounded-3xl border border-outline-variant/50 bg-surface-container-low/80 p-6">
        <h2 className="font-display text-xl font-bold text-on-surface">Knowledge snapshot</h2>
        <ul className="mt-4 grid gap-2 sm:grid-cols-2">
          {knowledge.map((k, i) => (
            <li key={`${k.kind}-${i}`} className="rounded-xl bg-surface-container/80 px-3 py-2 text-sm">
              <span className="font-mono text-xs text-primary">{k.kind}</span>
              <div className="text-on-surface">{k.title}</div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
