import Link from "next/link";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { BRAND_NAME, BRAND_SUBHEAD, BRAND_TAGLINE } from "@/lib/brand";

const authEntry = getAuthEntryPath();

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
      { href: "/gtm", label: "Strategy" },
      { href: "/marketing", label: "Campaigns" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="relative mt-28 overflow-hidden border-t border-outline-variant bg-slate-deep text-on-surface">
      <div className="absolute inset-0 opacity-30 [background-image:linear-gradient(to_right,var(--outline-variant)_1px,transparent_1px),linear-gradient(to_bottom,var(--outline-variant)_1px,transparent_1px)] [background-size:40px_40px]" />
      <div className="absolute left-1/2 top-0 h-72 w-[min(760px,90vw)] -translate-x-1/2 rounded-full bg-gradient-to-r from-primary/10 via-secondary/5 to-transparent blur-3xl" />
      <div className="container-page relative z-[1] py-16 md:py-20">
        <div className="grid gap-12 md:grid-cols-4">
          <div className="md:col-span-2">
            <div className="inline-flex items-center gap-3">
              <span className="h-8 w-8 border border-primary/50 bg-primary/10 font-mono text-sm font-bold text-primary flex items-center justify-center select-none">S</span>
              <p className="font-display text-xl font-extrabold tracking-[-0.03em] text-on-surface uppercase">{BRAND_NAME}</p>
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
