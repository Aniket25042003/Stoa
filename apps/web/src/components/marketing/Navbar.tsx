"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { cn } from "@/lib/cn";

const nav = [
  { href: "/how-it-works", label: "How it works" },
  { href: "/pricing", label: "Pricing" },
  { href: "/faq", label: "FAQ" },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const shell = cn(
    "mx-auto flex max-w-7xl flex-col gap-3 rounded-2xl border px-4 py-3 transition-all duration-300 md:flex-row md:items-center md:justify-between md:gap-6 md:px-5",
    scrolled
      ? "border-outline-variant/70 bg-surface-container-low/80 shadow-soft backdrop-blur-xl"
      : "border-outline-variant/55 bg-surface-container-low/45 backdrop-blur-md"
  );

  return (
    <header className="sticky top-0 z-50 px-4 py-3 md:px-6">
      <div className={shell}>
        {/* w-full + md grid: logo | centered nav | right-aligned CTAs (fixes collapsed row / buttons hugging left on desktop) */}
        <div className="grid w-full min-w-0 grid-cols-[minmax(0,1fr)_auto] items-center gap-3 md:grid-cols-[auto_1fr_auto] md:gap-6">
          <Link
            href="/"
            className="group inline-flex min-w-0 items-center gap-3 justify-self-start"
            aria-label="nexara home"
          >
            <span className="relative flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-primary via-indigo-pulse to-violet-pulse shadow-glow">
              <span className="absolute inset-0 bg-[radial-gradient(circle_at_35%_20%,rgb(255_255_255_/_0.55),transparent_34%)]" />
              <span className="relative font-mono text-sm font-semibold text-white">N</span>
            </span>
            <span className="truncate font-display text-lg font-extrabold tracking-[-0.03em] text-on-surface">nexara</span>
          </Link>

          <nav className="hidden items-center justify-center gap-7 justify-self-center md:flex" aria-label="Primary">
            {nav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="group relative shrink-0 font-mono text-xs font-semibold uppercase tracking-[0.1em] text-on-surface-variant transition-colors hover:text-primary"
              >
                {item.label}
                <span className="absolute -bottom-2 left-0 h-0.5 w-0 rounded-full bg-gradient-to-r from-primary to-secondary transition-all duration-300 group-hover:w-full" />
              </Link>
            ))}
          </nav>

          <div className="flex shrink-0 items-center justify-end gap-2 justify-self-end">
            <ThemeToggle />
            <Link href="/login" className="btn-nav-purple px-3 py-2 text-sm">
              Sign in
            </Link>
            <Link href="/login" className="btn-nav-purple hidden px-4 py-2 text-sm sm:inline-flex">
              Start free
            </Link>
          </div>
        </div>

        <nav
          className="flex items-center justify-center gap-5 overflow-x-auto pb-0.5 [-ms-overflow-style:none] [scrollbar-width:none] md:hidden [&::-webkit-scrollbar]:hidden"
          aria-label="Primary mobile"
        >
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="shrink-0 font-mono text-[11px] font-semibold uppercase tracking-[0.1em] text-on-surface-variant transition-colors hover:text-primary"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
