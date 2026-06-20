/**
 * @file apps/web/src/components/marketing/Footer.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies Next.js, React
 */
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowRight } from "lucide-react";
import { BrandLogo } from "@/components/product/BrandLogo";
import { getAuthEntryPath, getMarketingCta } from "@/lib/auth-entry";
import { BRAND_NAME, BRAND_SUBHEAD, BRAND_TAGLINE } from "@/lib/brand";
import { isMarketingV2Page } from "@/lib/marketing-v2";

const authEntry = getAuthEntryPath();
const marketingCta = getMarketingCta();

const productLinks = [
  { href: "/see-it-in-action", label: "See it in action" },
  { href: "/pricing", label: "Pricing" },
  { href: "/faq", label: "FAQ" },
];

const cols = [
  {
    title: "Product",
    links: [
      { href: "/see-it-in-action", label: "See it in action" },
      { href: "/pricing", label: "Pricing" },
      { href: "/faq", label: "FAQ" },
    ],
  },
  {
    title: "App",
    links: [
      { href: authEntry, label: "Sign in" },
      { href: "/dashboard", label: "Dashboard" },
      { href: "/intelligence", label: "Intelligence" },
      { href: "/campaigns", label: "Campaigns" },
    ],
  },
];

/**
 * Handles footer behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function Footer() {
  const pathname = usePathname();
  const isV2 = isMarketingV2Page(pathname);

  if (isV2) {
    return (
      <footer className="relative overflow-hidden border-t border-mkt-ink/[0.06] bg-mkt-dark-band text-mkt-dark-ink">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.12]"
          aria-hidden
          style={{
            backgroundImage:
              "linear-gradient(rgba(242,240,235,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(242,240,235,0.08) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />
        <div className="pointer-events-none absolute left-1/2 top-0 h-48 w-[min(640px,90vw)] -translate-x-1/2 -translate-y-1/2 rounded-full bg-mkt-accent/20 blur-3xl" />

        <div className="relative z-10 mx-auto max-w-7xl px-4 py-14 md:px-8 md:py-16">
          <div className="grid gap-12 md:grid-cols-[1.4fr_1fr_1fr]">
            <div>
              <div className="inline-flex items-center">
                <BrandLogo variant="icon" size="sm" />
              </div>
              <p className="mt-5 max-w-sm font-syne text-xl font-extrabold uppercase leading-tight tracking-tight text-mkt-dark-ink">
                {BRAND_TAGLINE}
              </p>
              <p className="mt-3 max-w-md font-dm-sans text-sm leading-relaxed text-mkt-dark-ink/65">
                {BRAND_SUBHEAD}
              </p>
            </div>

            <div>
              <p className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.22em] text-mkt-accent-warm">
                Explore
              </p>
              <ul className="mt-4 space-y-3">
                {productLinks.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="font-dm-sans text-sm text-mkt-dark-ink/70 transition-colors hover:text-mkt-dark-ink"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            <div className="flex flex-col justify-between gap-6">
              <div>
                <p className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.22em] text-mkt-accent">
                  Get started
                </p>
                <p className="mt-3 font-dm-sans text-sm leading-relaxed text-mkt-dark-ink/65">
                  {marketingCta.footerDescription}
                </p>
              </div>
              <Link
                href={marketingCta.href}
                className="group inline-flex w-fit items-center gap-2 rounded-sm bg-mkt-accent px-5 py-3 font-dm-sans text-[10px] font-bold uppercase tracking-widest text-mkt-dark-ink shadow-[0_8px_24px_rgba(79,70,229,0.35)] transition-all hover:bg-[#4338CA]"
              >
                {marketingCta.buttonLabel}
                <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </div>
          </div>

          <div className="mt-12 flex flex-col items-center justify-between gap-3 border-t border-mkt-dark-ink/10 pt-8 md:flex-row">
            <p className="font-dm-sans text-[10px] text-mkt-dark-ink/45">
              © {new Date().getFullYear()} {BRAND_NAME}. All rights reserved.
            </p>
            <p className="font-dm-sans text-[10px] uppercase tracking-[0.15em] text-mkt-dark-ink/35">
              Connect. Retrieve. Ship.
            </p>
          </div>
        </div>
      </footer>
    );
  }

  return (
    <footer className="relative mt-28 overflow-hidden border-t border-outline-variant bg-slate-deep text-on-surface">
      <div className="absolute inset-0 opacity-30 [background-image:linear-gradient(to_right,var(--outline-variant)_1px,transparent_1px),linear-gradient(to_bottom,var(--outline-variant)_1px,transparent_1px)] [background-size:40px_40px]" />
      <div className="absolute left-1/2 top-0 h-72 w-[min(760px,90vw)] -translate-x-1/2 rounded-full bg-gradient-to-r from-primary/10 via-secondary/5 to-transparent blur-3xl" />
      <div className="container-page relative z-[1] py-16 md:py-20">
        <div className="grid gap-12 md:grid-cols-4">
          <div className="md:col-span-2">
            <div className="inline-flex items-center">
              <BrandLogo variant="icon" size="sm" />
            </div>
            <p className="mt-4 max-w-md text-sm leading-relaxed text-on-surface-variant/90">{BRAND_TAGLINE}</p>
            <p className="mt-2 max-w-md text-xs leading-relaxed text-on-surface-variant/70 font-mono">{BRAND_SUBHEAD}</p>
          </div>
          {cols.map((col) => (
            <div key={col.title} className="font-mono text-xs">
              <p className="text-primary font-bold uppercase tracking-widest">[{col.title}]</p>
              <ul className="mt-4 space-y-3">
                {col.links.map((l) => (
                  <li key={l.href}>
                    <Link href={l.href} className="text-on-surface-variant hover:text-primary transition-colors duration-200">
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <p className="mt-12 border-t border-outline-variant/60 pt-8 font-mono text-xs text-on-surface-variant/60">
          © {new Date().getFullYear()} {BRAND_NAME}. {BRAND_TAGLINE}
        </p>
      </div>
    </footer>
  );
}
