import Link from "next/link";
import { redirect } from "next/navigation";
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
    <main>
      <div className="card">
        <h1>Dashboard</h1>
        <p style={{ color: "var(--muted)" }}>Signed in as {session.user.email}</p>
        <p>
          <Link className="btn" href="/runs/new">
            New GTM run
          </Link>
        </p>
      </div>
      <div className="card">
        <h2>Recent runs</h2>
        {runs.length === 0 ? (
          <p style={{ color: "var(--muted)" }}>No runs yet (is the API running and CORS configured?).</p>
        ) : (
          <ul>
            {runs.map((r) => (
              <li key={r.id}>
                <Link href={`/runs/${r.id}`}>
                  {r.id.slice(0, 8)}… — {r.status}
                </Link>{" "}
                <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>{r.created_at}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
