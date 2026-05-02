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
    <main>
      <div className="card">
        <h1>New GTM run</h1>
        <p style={{ color: "var(--muted)" }}>
          Describe your product. The multi-agent pipeline will research, reason, and draft a GTM document.
        </p>
        <NewRunForm accessToken={session.access_token} />
        <p style={{ marginTop: "1rem" }}>
          <Link href="/dashboard">Back</Link>
        </p>
      </div>
    </main>
  );
}
