"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { createClient } from "@/lib/supabase/client";
import { BRAND_NAME, BRAND_SUBHEAD, BRAND_TAGLINE } from "@/lib/brand";
import { cn } from "@/lib/cn";

export default function WaitlistPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [registered, setRegistered] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email) return;

    setLoading(true);
    setLogs([
      "SYS: Connecting to waitlist node...",
      "SYS: Initializing registration request...",
      "INGEST: Checking email uniqueness..."
    ]);

    const supabase = createClient();
    const { error } = await supabase.from("waitlist").insert([{ name, email }]);

    setTimeout(() => {
      if (error) {
        if (error.code === "23505") {
          // Unique constraint violation (already registered)
          setLogs((prev) => [
            ...prev,
            "WARN: Email already registered in waitlist queue.",
            "STATUS: In queue.",
            "INFO: Re-compiling target workspace keys is not necessary."
          ]);
          setRegistered(true);
        } else {
          setLogs((prev) => [
            ...prev,
            `ERROR: Compilation failed: ${error.message}`,
            "SYS: Please verify network status and try again."
          ]);
        }
      } else {
        const queuePos = Math.floor(Math.random() * 80) + 420;
        setLogs((prev) => [
          ...prev,
          "SUCCESS: Registered in waitlist queue.",
          `QUEUE_POSITION: #${queuePos}`,
          "STATUS: Active.",
          "INFO: We will notify you when system keys are compiled."
        ]);
        setRegistered(true);
        setName("");
        setEmail("");
      }
      setLoading(false);
    }, 1500); // Add a small delay for a realistic compiler feel
  };

  return (
    <div className="relative min-h-screen overflow-hidden px-4 py-10 md:px-6">
      {/* Background canvas elements */}
      <div className="absolute inset-0 -z-10 grid-bg dark:starfield" />
      <div className="absolute left-1/2 top-0 -z-10 h-[520px] w-[min(760px,92vw)] -translate-x-1/2 rounded-full bg-gradient-to-r from-primary/10 via-secondary/5 to-transparent blur-3xl" />

      <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-7xl flex-col gap-10 lg:flex-row lg:items-center lg:gap-16">
        
        {/* Left Side: Rebranding Coming Soon Info */}
        <div className="flex-1 space-y-7 lg:max-w-lg">
          <Link href="/" className="inline-flex items-center gap-3">
            <span className="relative flex h-8 w-8 shrink-0 items-center justify-center border border-primary/40 bg-primary/10 font-mono text-sm font-black text-primary select-none">
              S
            </span>
            <span className="font-display text-xl font-extrabold tracking-[-0.03em] text-on-surface uppercase">{BRAND_NAME}</span>
          </Link>
          
          <div className="font-mono">
            <div className="inline-flex items-center gap-2 border border-primary/30 bg-primary/5 px-3 py-1 mb-4">
              <span className="h-1.5 w-1.5 bg-primary animate-pulse" />
              <p className="text-[10px] uppercase font-bold tracking-widest text-primary">STOA_CLOSED_BUILD</p>
            </div>
            <h1 className="mt-4 font-display text-4xl font-extrabold leading-tight tracking-tight text-on-surface md:text-5xl uppercase">
              Closed Compilation Mode
            </h1>
            <p className="mt-5 text-sm leading-relaxed text-on-surface-variant">{BRAND_TAGLINE}</p>
            <p className="mt-2 text-xs leading-relaxed text-on-surface-variant/80">{BRAND_SUBHEAD}</p>
            <p className="mt-6 text-xs text-on-surface-variant font-bold">
              We are currently scaling workspace components. Fill out the console fields to compile your waitlist keys.
            </p>
          </div>
        </div>

        {/* Right Side: Waitlist form / Console stdout */}
        <div className="flex flex-1 justify-center lg:justify-end">
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
            className="w-full max-w-md border border-outline-variant bg-surface-container-lowest p-6 shadow-card font-mono text-xs text-on-surface flex flex-col"
          >
            {/* Header tab */}
            <div className="flex items-center justify-between border-b border-outline-variant/60 pb-2.5 mb-6 select-none">
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 bg-primary" />
                <span className="h-2 w-2 bg-secondary" />
                <span className="h-2 w-2 bg-outline-variant" />
                <span className="ml-1.5 text-[9px] text-on-surface-variant">stoa@waitlist-register:~</span>
              </div>
              <span className="text-[9px] text-primary font-bold">REGISTRATION</span>
            </div>

            {/* Waitlist Form */}
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div>
                <label className="text-[10px] text-on-surface-variant block mb-1">USER_NAME</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={loading || (registered && logs.length > 3)}
                  placeholder="ENTER YOUR NAME"
                  className="w-full bg-surface border border-outline-variant px-3 py-2 text-xs text-on-surface focus:outline-none focus:border-primary disabled:opacity-50 font-mono uppercase placeholder:opacity-30"
                />
              </div>

              <div>
                <label className="text-[10px] text-on-surface-variant block mb-1">USER_EMAIL</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading || (registered && logs.length > 3)}
                  placeholder="ENTER YOUR EMAIL"
                  className="w-full bg-surface border border-outline-variant px-3 py-2 text-xs text-on-surface focus:outline-none focus:border-primary disabled:opacity-50 font-mono uppercase placeholder:opacity-30"
                />
              </div>

              <button
                type="submit"
                disabled={loading || (registered && logs.length > 3)}
                className="w-full border border-primary bg-primary/10 py-2.5 font-bold uppercase tracking-wider text-primary hover:bg-primary hover:text-surface transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed text-[10px] flex items-center justify-center gap-2 cursor-pointer"
              >
                {loading ? "COMPILING_REGISTRATION..." : "SUBMIT_REGISTRATION.SH"}
              </button>
            </form>

            {/* Console Log stream */}
            {logs.length > 0 && (
              <div className="mt-6 border-t border-outline-variant/60 pt-4 flex flex-col gap-2">
                <div className="text-[9px] text-secondary font-bold uppercase select-none">STDOUT_STREAM:</div>
                <div className="bg-surface border border-outline-variant/40 p-3 flex flex-col gap-1.5 overflow-y-auto max-h-36 leading-relaxed select-text font-mono text-[10px]">
                  {logs.map((log, index) => {
                    let colorClass = "text-on-surface-variant";
                    if (log.startsWith("SYS:")) colorClass = "text-secondary";
                    if (log.startsWith("SUCCESS:")) colorClass = "text-emerald-400 font-semibold";
                    if (log.startsWith("WARN:")) colorClass = "text-primary/95 font-semibold";
                    if (log.startsWith("ERROR:")) colorClass = "text-error font-semibold";
                    
                    return (
                      <div key={index} className={cn("flex gap-2 items-start", colorClass)}>
                        <span className="text-outline-variant/50 select-none">{(index + 1).toString().padStart(2, "0")}</span>
                        <span>{log}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <p className="mt-8 text-center text-xs select-none">
              <Link href="/" className="font-bold text-primary hover:text-secondary transition-colors uppercase tracking-wider">
                [BACK_HOME]
              </Link>
            </p>
          </motion.div>
        </div>

      </div>
    </div>
  );
}
