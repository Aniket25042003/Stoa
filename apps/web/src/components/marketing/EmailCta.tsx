"use client";

import Link from "next/link";
import { useState } from "react";

export function EmailCta() {
  const [email, setEmail] = useState("");
  const href = email.trim() ? `/login?email=${encodeURIComponent(email.trim())}` : "/login";

  return (
    <div className="flex max-w-xl flex-col gap-3 sm:flex-row sm:items-center">
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="you@company.com"
        className="flex-1 rounded-lg border border-mist bg-cream px-4 py-3 text-sm text-ink placeholder:text-ink/40 focus:border-slate focus:outline-none focus:ring-2 focus:ring-slate/30"
      />
      <Link
        href={href}
        className="inline-flex shrink-0 items-center justify-center rounded-lg bg-slate px-5 py-3 text-center text-sm font-semibold text-cream shadow-glow transition-opacity hover:opacity-90"
      >
        Continue
      </Link>
    </div>
  );
}
