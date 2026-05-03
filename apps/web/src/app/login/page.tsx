"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { createClient } from "@/lib/supabase/client";
import { ActivityTickerTeaser } from "@/components/marketing/ActivityTickerTeaser";

function LoginForm() {
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const e = searchParams.get("email");
    if (e) setEmail(e);
    const err = searchParams.get("error");
    if (err) setMsg(err);
  }, [searchParams]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    setLoading(true);
    const supabase = createClient();
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    const emailRedirectTo = origin ? `${origin}/auth/callback?next=${encodeURIComponent("/dashboard")}` : undefined;
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo },
    });
    setLoading(false);
    if (error) setMsg(error.message);
    else setMsg("Check your email for the magic link.");
  }

  return (
    <div className="relative z-10 mx-auto flex min-h-screen max-w-6xl flex-col gap-10 px-4 py-12 lg:flex-row lg:items-center lg:gap-16 lg:px-6 lg:py-16">
      <div className="flex-1 space-y-6 lg:max-w-md">
        <p className="font-mono text-xs uppercase tracking-[0.28em] text-slate">GTM Agent</p>
        <h1 className="text-3xl font-semibold tracking-tight text-ink md:text-4xl">Sign in with a magic link</h1>
        <p className="text-sm leading-relaxed text-ink/70">
          No password. We email you a one-time link that drops you on the dashboard.
        </p>
        <div className="hidden lg:block">
          <ActivityTickerTeaser />
        </div>
      </div>

      <div className="flex flex-1 justify-center lg:justify-end">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="w-full max-w-md rounded-2xl border border-mist bg-cream/95 p-6 shadow-sm backdrop-blur-sm md:p-8"
        >
          <h2 className="text-lg font-semibold text-ink">Email</h2>
          <form onSubmit={onSubmit} className="mt-4 space-y-4">
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-mist bg-cream px-3 py-2.5 text-sm text-ink focus:border-slate focus:outline-none focus:ring-2 focus:ring-slate/30"
              placeholder="you@company.com"
            />
            <motion.button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center rounded-lg bg-slate py-2.5 text-sm font-semibold text-cream shadow-glow transition-opacity hover:opacity-90 disabled:opacity-50"
              whileTap={{ scale: 0.98 }}
            >
              {loading ? "Sending…" : "Send link"}
            </motion.button>
          </form>
          {msg ? (
            <motion.p
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 text-sm text-ink/80"
            >
              {msg}
            </motion.p>
          ) : null}
          <p className="mt-6 text-center text-sm">
            <Link href="/" className="font-medium text-slate hover:underline">
              ← Home
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="relative z-10 flex min-h-screen items-center justify-center px-4 text-sm text-ink/60">
          Loading sign-in…
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
