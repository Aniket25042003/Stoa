"use client";

import Link from "next/link";
import { ThemeToggle } from "@/components/ThemeToggle";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { BRAND_LOGO_LETTER, BRAND_NAME } from "@/lib/brand";

const nav = [
  { href: "/see-it-in-action", label: "See it in action", index: "01" },
  { href: "/pricing", label: "Pricing", index: "02" },
  { href: "/faq", label: "FAQ", index: "03" },
];

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-outline-variant bg-surface/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 md:px-6">
        <Link
          href="/"
          className="group inline-flex min-w-0 items-center gap-3"
          aria-label={`${BRAND_NAME} home`}
        >
          <span className="relative flex h-8 w-8 shrink-0 items-center justify-center border border-primary/40 bg-primary/10 font-mono text-sm font-black text-primary select-none">
            {BRAND_LOGO_LETTER}
          </span>
          <span className="truncate font-display text-base font-extrabold tracking-[0.05em] text-on-surface uppercase">
            {BRAND_NAME}
          </span>
        </Link>

        <nav className="hidden items-center justify-center gap-8 md:flex" aria-label="Primary">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="group relative shrink-0 font-mono text-xs font-semibold uppercase tracking-[0.1em] text-on-surface-variant transition-colors hover:text-primary"
            >
              <span className="text-secondary/80 mr-1 transition-colors group-hover:text-primary">[{item.index}]</span>
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="flex shrink-0 items-center justify-end gap-3">
          <ThemeToggle />
          <Link href="/waitlist" className="btn-nav-purple px-3 py-1.5 text-xs uppercase tracking-wider font-mono">
            Sign in
          </Link>
          <Link href="/waitlist" className="btn-primary hidden px-4 py-1.5 text-xs uppercase tracking-wider font-mono sm:inline-flex">
            Start free
          </Link>
        </div>
      </div>

      {/* Mobile nav subbar */}
      <nav
        className="flex items-center justify-center gap-6 border-t border-outline-variant/30 py-2.5 md:hidden"
        aria-label="Primary mobile"
      >
        {nav.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="shrink-0 font-mono text-[10px] font-semibold uppercase tracking-[0.1em] text-on-surface-variant transition-colors hover:text-primary"
          >
            <span className="text-secondary/80 mr-1">[{item.index}]</span>
            {item.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
