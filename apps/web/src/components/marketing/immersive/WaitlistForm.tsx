"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export function WaitlistForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
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
        throw new Error(body?.detail || "Registration failed. Please try again.");
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
    <div className="w-full max-w-md rounded-sm border border-mkt-ink/5 bg-mkt-surface/85 p-8 shadow-[0_30px_70px_rgba(20,20,26,0.03)] backdrop-blur-xl">
      <AnimatePresence mode="wait">
        {status === "success" ? (
          <motion.div
            key="success"
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.96 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="text-center py-6"
          >
            <div className="mx-auto h-12 w-12 rounded-full bg-[#4F46E5]/10 flex items-center justify-center mb-6">
              <svg className="h-6 w-6 text-[#4F46E5]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="font-syne mb-3 text-xl font-bold text-mkt-ink">You&apos;re on the list.</h3>
            <p className="font-dm-sans text-sm leading-relaxed text-mkt-muted">
              We&apos;ll be in touch as soon as Stoa early access opens.
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
            <div className="text-center mb-8">
              <h2 className="font-syne text-2xl font-bold tracking-tight text-[#14141A]">
                Request Access
              </h2>
              <p className="font-dm-sans text-xs text-[#6B6F7D] mt-2">
                Join our private release queue.
              </p>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="name" className="font-mono text-[9px] tracking-widest text-[#6B6F7D] uppercase font-bold">
                Full Name
              </label>
              <input
                id="name"
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={loading}
                placeholder="Jane Doe"
                className="w-full bg-[#F8F6F2] border border-[#14141A]/10 px-4 py-3 text-sm text-[#14141A] rounded-sm transition-all focus:outline-none focus:border-[#4F46E5] focus:ring-1 focus:ring-[#4F46E5] disabled:opacity-50"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="email" className="font-mono text-[9px] tracking-widest text-[#6B6F7D] uppercase font-bold">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
                placeholder="jane@example.com"
                className="w-full bg-[#F8F6F2] border border-[#14141A]/10 px-4 py-3 text-sm text-[#14141A] rounded-sm transition-all focus:outline-none focus:border-[#4F46E5] focus:ring-1 focus:ring-[#4F46E5] disabled:opacity-50"
              />
            </div>

            {status === "error" && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-3 bg-[#E85D4C]/10 border border-[#E85D4C]/25 text-[#E85D4C] text-xs font-semibold rounded-sm leading-relaxed"
              >
                {errorMsg}
              </motion.div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#4F46E5] text-[#F2F0EB] py-3 text-sm font-bold tracking-wider rounded-sm transition-all hover:bg-[#4338CA] hover:shadow-[0_10px_25px_-5px_rgba(79,70,229,0.2)] active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer font-syne uppercase"
            >
              {loading ? "Registering..." : "Join the waitlist"}
            </button>
          </motion.form>
        )}
      </AnimatePresence>
    </div>
  );
}
