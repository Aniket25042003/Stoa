"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SolidButton } from "@/components/marketing/v3/Buttons";

export function WaitlistForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<"idle" | "success" | "already_registered" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email) return;

    setLoading(true);
    setStatus("idle");
    setErrorMsg("");

    try {
      const res = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email }),
      });

      const body = (await res.json().catch(() => null)) as { status?: string; detail?: string } | null;

      if (!res.ok) {
        const detail =
          typeof body?.detail === "string"
            ? body.detail
            : res.status === 429
              ? "Too many attempts. Please wait a minute and try again."
              : "Registration failed. Please try again.";
        throw new Error(detail);
      }

      if (body?.status === "already_registered") {
        setStatus("already_registered");
        return;
      }

      setStatus("success");
      setName("");
      setEmail("");
    } catch (err: unknown) {
      console.error(err);
      setStatus("error");
      const message = err instanceof Error ? err.message : "Failed to join waitlist. Please check network connections.";
      setErrorMsg(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md rounded-2xl border border-mkt-border bg-mkt-surface-elevated p-8 shadow-[0_20px_60px_-20px_rgba(0,0,0,0.12)]">
      <AnimatePresence mode="wait">
        {status === "success" ? (
          <motion.div
            key="success"
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.96 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="py-6 text-center"
          >
            <div className="mx-auto mb-6 flex h-12 w-12 items-center justify-center rounded-full bg-mkt-ink/5">
              <svg className="h-6 w-6 text-mkt-ink" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="mb-3 text-xl font-semibold text-mkt-ink">You&apos;re on the list.</h3>
            <p className="text-sm leading-relaxed text-mkt-muted">
              We&apos;ll be in touch as soon as Stoa early access opens.
            </p>
          </motion.div>
        ) : status === "already_registered" ? (
          <motion.div
            key="already-registered"
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.96 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="py-6 text-center"
          >
            <div className="mx-auto mb-6 flex h-12 w-12 items-center justify-center rounded-full bg-mkt-ink/5">
              <svg className="h-6 w-6 text-mkt-ink" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h3 className="mb-3 text-xl font-semibold text-mkt-ink">You&apos;re already on the waitlist.</h3>
            <p className="text-sm leading-relaxed text-mkt-muted">
              We&apos;ve got your email. We&apos;ll notify you as soon as early access opens.
            </p>
          </motion.div>
        ) : (
          <motion.form
            key="form"
            onSubmit={handleSubmit}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-5"
          >
            <div className="mb-8 text-center">
              <h2 className="text-2xl font-semibold tracking-tight text-mkt-ink">Request access</h2>
              <p className="mt-2 text-sm text-mkt-muted">Join our private release queue.</p>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="name" className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">
                Full name
              </label>
              <input
                id="name"
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={loading}
                placeholder="Jane Doe"
                className="w-full rounded-xl border border-mkt-border bg-mkt-surface px-4 py-3 text-sm text-mkt-ink transition-all focus:border-mkt-ink focus:outline-none focus:ring-1 focus:ring-mkt-ink disabled:opacity-50"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="email" className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">
                Email address
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
                placeholder="jane@example.com"
                className="w-full rounded-xl border border-mkt-border bg-mkt-surface px-4 py-3 text-sm text-mkt-ink transition-all focus:border-mkt-ink focus:outline-none focus:ring-1 focus:ring-mkt-ink disabled:opacity-50"
              />
            </div>

            {status === "error" && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-xl border border-red-200 bg-red-50 p-3 text-xs font-medium leading-relaxed text-red-700"
              >
                {errorMsg}
              </motion.div>
            )}

            <SolidButton type="submit" disabled={loading} variant="dark" className="w-full justify-center py-3">
              {loading ? "Registering..." : "Join the waitlist"}
            </SolidButton>
          </motion.form>
        )}
      </AnimatePresence>
    </div>
  );
}
