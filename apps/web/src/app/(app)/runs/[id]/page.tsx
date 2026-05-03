import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { RunDetail } from "./ui";

export default async function RunDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
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
        <h1 className="mt-4 font-mono text-2xl font-semibold tracking-tight text-ink md:text-3xl">Run {id.slice(0, 8)}…</h1>
      </div>
      <RunDetail runId={id} accessToken={session.access_token} />
    </div>
  );
}
