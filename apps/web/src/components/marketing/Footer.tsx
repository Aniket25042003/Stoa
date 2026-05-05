import Link from "next/link";

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
      { href: "/runs/new", label: "New run" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="relative mt-28 overflow-hidden bg-slate-deep text-inverse-on-surface">
      <div className="absolute inset-0 opacity-30 [background-image:linear-gradient(to_right,rgb(255_255_255_/_0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgb(255_255_255_/_0.08)_1px,transparent_1px)] [background-size:40px_40px]" />
      <div className="absolute left-1/2 top-0 h-72 w-[min(760px,90vw)] -translate-x-1/2 rounded-full bg-gradient-to-r from-primary/30 via-violet-pulse/20 to-transparent blur-3xl" />
      <div className="container-page relative py-16 md:py-20">
        <div className="grid gap-12 md:grid-cols-4">
          <div className="md:col-span-2">
            <div className="inline-flex items-center gap-3">
              <span className="h-9 w-9 rounded-xl bg-gradient-to-br from-primary to-violet-pulse shadow-glow" />
              <p className="font-display text-xl font-extrabold tracking-[-0.03em]">GTM Agent</p>
            </div>
            <p className="mt-4 max-w-md text-sm leading-7 text-inverse-on-surface/72">
              Autonomous research, layered reasoning, and founder-ready GTM reports with transparent agent activity and review gates.
            </p>
          </div>
          {cols.map((col) => (
            <div key={col.title}>
              <p className="font-mono text-xs font-semibold uppercase tracking-[0.14em] text-inverse-primary">{col.title}</p>
              <ul className="mt-4 space-y-3 text-sm">
                {col.links.map((l) => (
                  <li key={l.href}>
                    <Link href={l.href} className="text-inverse-on-surface/78 transition-colors hover:text-white">
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <p className="mt-12 border-t border-white/10 pt-8 font-mono text-xs text-inverse-on-surface/48">
          © {new Date().getFullYear()} GTM Agent. High-performance GTM workflows for focused teams.
        </p>
      </div>
    </footer>
  );
}
