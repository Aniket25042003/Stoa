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
    <footer className="relative mt-24 border-t border-mist bg-ink text-cream">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-[0.08]"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgb(203 203 203 / 35%) 1px, transparent 1px), linear-gradient(to bottom, rgb(203 203 203 / 35%) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />
      <div className="relative mx-auto max-w-6xl px-4 py-16 md:px-6">
        <div className="grid gap-12 md:grid-cols-4">
          <div className="md:col-span-2">
            <p className="text-lg font-semibold tracking-tight">GTM Agent</p>
            <p className="mt-3 max-w-md text-sm leading-relaxed text-cream/75">
              Autonomous research, layered reasoning, and a founder-ready GTM document — with full transparency and
              traces you can debug.
            </p>
          </div>
          {cols.map((col) => (
            <div key={col.title}>
              <p className="font-mono text-xs uppercase tracking-[0.2em] text-cream/60">{col.title}</p>
              <ul className="mt-4 space-y-2 text-sm">
                {col.links.map((l) => (
                  <li key={l.href}>
                    <Link href={l.href} className="text-cream/85 transition-colors hover:text-cream">
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <p className="mt-12 border-t border-mist/40 pt-8 font-mono text-xs text-cream/50">
          © {new Date().getFullYear()} GTM Agent. Built for founders.
        </p>
      </div>
    </footer>
  );
}
