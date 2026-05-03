import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { NewRunForm } from "./ui";

export default async function NewRunPage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) redirect("/login");

  return (
    <div className="space-y-6">
      <div>
        <Link href="/dashboard" className="text-sm font-medium text-slate hover:underline">
          ← Dashboard
        </Link>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight text-ink md:text-4xl">New GTM run</h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink/70">
          Describe your product. The multi-agent pipeline will draft a master plan for your approval, then research,
          reason, and write your GTM document.
        </p>
      </div>
      <div className="rounded-2xl border border-mist bg-cream/95 p-6 shadow-sm md:p-8">
        <NewRunForm accessToken={session.access_token} />
      </div>
    </div>
  );
}
