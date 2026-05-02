"use client";

import { useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    const supabase = createClient();
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: typeof window !== "undefined" ? `${window.location.origin}/dashboard` : undefined },
    });
    if (error) setMsg(error.message);
    else setMsg("Check your email for the magic link.");
  }

  return (
    <main>
      <div className="card">
        <h1>Sign in</h1>
        <p style={{ color: "var(--muted)" }}>Magic link via Supabase Auth.</p>
        <form onSubmit={onSubmit}>
          <label htmlFor="email">Email</label>
          <input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          <p style={{ marginTop: "1rem" }}>
            <button type="submit">Send link</button>
          </p>
        </form>
        {msg && <p style={{ marginTop: "0.75rem" }}>{msg}</p>}
        <p style={{ marginTop: "1rem" }}>
          <Link href="/">Home</Link>
        </p>
      </div>
    </main>
  );
}
