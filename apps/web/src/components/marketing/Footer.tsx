import Link from "next/link";
import { BRAND_NAME, BRAND_SUBHEAD, BRAND_TAGLINE } from "@/lib/brand";

const cols = [
  {
    title: "Product",
    links: [
      { href: "/how-it-works", label: "How it works" },
      { href: "/pricing", label: "Pricing" },
      { href: "/faq", label: "FAQ" },
    ],
  },
  {
    title: "App",
    links: [
      { href: "/login", label: "Sign in" },
      { href: "/dashboard", label: "Dashboard" },
      { href: "/gtm", label: "GTM" },
      { href: "/marketing", label: "Marketing" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="relative mt-28 overflow-hidden bg-slate-deep text-white">
      <div className="absolute inset-0 opacity-30 [background-image:linear-gradient(to_right,rgb(255_255_255_/_0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgb(255_255_255_/_0.08)_1px,transparent_1px)] [background-size:40px_40px]" />
      <div className="absolute left-1/2 top-0 h-72 w-[min(760px,90vw)] -translate-x-1/2 rounded-full bg-gradient-to-r from-primary/30 via-violet-pulse/20 to-transparent blur-3xl" />
      <div className="container-page relative z-[1] py-16 md:py-20">
        <div className="grid gap-12 md:grid-cols-4">
          <div className="md:col-span-2">
            <div className="inline-flex items-center gap-3">
              <span className="h-9 w-9 rounded-xl bg-gradient-to-br from-primary to-violet-pulse shadow-glow" />
              <p className="font-display text-xl font-extrabold tracking-[-0.03em] text-white">{BRAND_NAME}</p>
            </div>
            <p className="mt-4 max-w-md text-sm leading-7 text-white/78">{BRAND_TAGLINE}</p>
            <p className="mt-3 max-w-md text-sm leading-7 text-white/62">{BRAND_SUBHEAD}</p>
          </div>
          {cols.map((col) => (
            <div key={col.title}>
              <p className="font-mono text-xs font-semibold uppercase tracking-[0.14em] text-[rgb(200,201,255)]">{col.title}</p>
              <ul className="mt-4 space-y-3 text-sm">
                {col.links.map((l) => (
                  <li key={l.href}>
                    <Link href={l.href} className="text-white/80 transition-colors hover:text-white">
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <p className="mt-12 border-t border-white/15 pt-8 font-mono text-xs text-white/45">
          © {new Date().getFullYear()} {BRAND_NAME}. {BRAND_TAGLINE}
        </p>
      </div>
    </footer>
  );
}
