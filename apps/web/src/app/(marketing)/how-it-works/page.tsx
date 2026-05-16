import Link from "next/link";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { SectionHeader } from "@/components/marketing/SectionHeader";
import { BRAND_SUBHEAD, BRAND_TAGLINE } from "@/lib/brand";

const steps = [
  {
    title: "Create a company workspace",
    body: "Add the basics once: who you serve, what you sell, where you compete, and the goals you care about right now.",
  },
  {
    title: "Build or upload your GTM plan",
    body: "Start from a guided plan or bring your own. Either way, the plan becomes a living strategy your team can revisit and improve.",
  },
  {
    title: "Chat with your GTM workspace",
    body: "Ask for positioning changes, ICP refinements, channel ideas, or launch priorities. Updates stay attached to the company you selected.",
  },
  {
    title: "Set your marketing foundation",
    body: "Capture brand voice, design notes, messaging preferences, and campaign context so future marketing work starts from the right baseline.",
  },
  {
    title: "Work through marketing tasks",
    body: "Brainstorm ads, draft copy, shape scripts, plan calendars, and organize campaign outputs without switching tools.",
  },
  {
    title: "Keep companies separate",
    body: "Each company has its own strategy, brand voice, chats, and assets, even when the same user manages multiple businesses.",
  },
];

const atAGlance = [
  "Secure sign-in",
  "Multiple companies in one account",
  "Separate context for every company",
  "GTM planning and marketing execution",
  "Editable plans and reusable campaign assets",
  "Simple tabs for Dashboard, GTM, and Marketing",
];

export default function HowItWorksPage() {
  return (
    <div className="container-page py-16 md:py-24">
      <RevealOnScroll>
        <SectionHeader
          eyebrow="How it works"
          title="From company context to GTM and marketing execution."
          lead={`${BRAND_TAGLINE} ${BRAND_SUBHEAD}`}
        />
      </RevealOnScroll>

      <div className="mt-10 rounded-3xl border border-outline-variant/55 bg-surface-container-low/75 p-5 lg:hidden">
        <p className="eyebrow text-[11px]">At a glance</p>
        <ul className="mt-3 space-y-2 text-sm leading-relaxed text-on-surface-variant">
          {atAGlance.map((line) => (
            <li key={line} className="flex gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-gradient-to-r from-primary to-violet-pulse" />
              {line}
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-16 lg:grid lg:grid-cols-[0.9fr_1.1fr] lg:gap-16">
        <aside className="relative mb-12 lg:mb-0">
          <div className="sticky top-28 hidden overflow-hidden rounded-3xl border border-white/10 bg-slate-deep p-8 shadow-card lg:block">
            <div className="absolute inset-0 opacity-25 [background-image:linear-gradient(to_right,rgb(255_255_255_/_0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgb(255_255_255_/_0.08)_1px,transparent_1px)] [background-size:36px_36px]" />
            <div className="relative text-white">
              <p className="font-mono text-xs font-semibold uppercase tracking-[0.14em] text-[rgb(200,201,255)]">At a glance</p>
              <ul className="mt-4 space-y-3 text-sm leading-relaxed text-white/78">
                {atAGlance.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
              <p className="mt-8 font-mono text-xs font-semibold uppercase tracking-[0.14em] text-[rgb(200,201,255)]">Flow</p>
              <pre className="mt-3 whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-white/64">
                {`Company profile
    -> GTM plan
    -> Marketing foundation
    -> Campaign work
    -> Team-ready outputs`}
              </pre>
            </div>
          </div>
        </aside>
        <div className="space-y-10">
          {steps.map((s, i) => (
            <RevealOnScroll key={s.title} delay={0.04 * i}>
              <article className="relative rounded-3xl p-7 card-glass md:p-8">
                <div className="absolute left-0 top-8 h-10 w-1 rounded-r-full bg-gradient-to-b from-primary to-violet-pulse" />
                <p className="eyebrow">Step {String(i + 1).padStart(2, "0")}</p>
                <h2 className="mt-4 font-display text-3xl font-bold tracking-[-0.035em] text-on-surface md:text-4xl">{s.title}</h2>
                <p className="mt-4 text-base leading-8 text-on-surface-variant md:text-lg">{s.body}</p>
              </article>
            </RevealOnScroll>
          ))}
        </div>
      </div>

      <RevealOnScroll>
        <div className="mt-20 rounded-3xl p-8 text-center card-glass">
          <p className="font-display text-xl font-bold text-on-surface">Try it now</p>
          <p className="mt-2 text-sm text-on-surface-variant">{BRAND_SUBHEAD}</p>
          <Link href="/login" className="btn-primary mt-6 px-6 py-3 text-sm">
            Get started
          </Link>
        </div>
      </RevealOnScroll>
    </div>
  );
}
