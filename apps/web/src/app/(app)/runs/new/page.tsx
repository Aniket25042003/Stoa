import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { NewRunForm } from "./ui";

export default async function NewRunPage({ searchParams }: { searchParams: Promise<{ company_id?: string }> }) {
  const sp = await searchParams;
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) redirect("/login");

  return (
    <div className="space-y-7">
      <div className="rounded-[2rem] bg-slate-deep p-7 text-white shadow-card md:p-10">
        <Link href="/dashboard" className="font-mono text-xs font-semibold uppercase tracking-[0.12em] text-inverse-primary hover:text-white">
          Back to dashboard
        </Link>
        <h1 className="mt-5 font-display text-4xl font-extrabold tracking-[-0.045em] md:text-5xl">New GTM run</h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-white/68">
          Describe your product and goals. nexara will draft a GTM plan for your review and turn it into a document your team can use.
        </p>
      </div>
      <div className="rounded-3xl p-6 card-glass md:p-8">
        <NewRunForm accessToken={session.access_token} defaultCompanyId={sp.company_id} />
      </div>
    </div>
  );
}
