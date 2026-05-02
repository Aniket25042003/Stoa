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
    <main>
      <div className="card">
        <p>
          <Link href="/dashboard">← Dashboard</Link>
        </p>
        <h1>Run {id.slice(0, 8)}…</h1>
        <RunDetail runId={id} accessToken={session.access_token} />
      </div>
    </main>
  );
}
