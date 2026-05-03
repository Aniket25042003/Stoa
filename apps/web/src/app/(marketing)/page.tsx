"use client";

import Link from "next/link";
import { AnimatedHeadline } from "@/components/marketing/AnimatedHeadline";
import { AgentHierarchyDiagram } from "@/components/marketing/AgentHierarchyDiagram";
import { EmailCta } from "@/components/marketing/EmailCta";
import { FeatureCard } from "@/components/marketing/FeatureCard";
import { GradientOrb } from "@/components/marketing/GradientOrb";
import { LiveActivityDemo } from "@/components/marketing/LiveActivityDemo";
import { Marquee } from "@/components/marketing/Marquee";
import { ReportPreviewCard } from "@/components/marketing/ReportPreviewCard";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { SectionHeader } from "@/components/marketing/SectionHeader";
import { BookOpen, PenLine, Radar } from "lucide-react";

const sources = [
  "Reddit",
  "X",
  "Tavily",
  "Jina",
  "SerpAPI",
  "LangSmith",
  "Supabase",
  "Redis",
];

export default function LandingPage() {
  return (
    <>
      <section className="relative overflow-hidden px-4 pb-20 pt-10 md:px-6 md:pb-28 md:pt-16">
        <GradientOrb />
        <div className="relative mx-auto max-w-6xl">
          <p className="font-mono text-xs uppercase tracking-[0.28em] text-slate">Build your GTM in a weekend</p>
          <AnimatedHeadline
            text="Your autonomous go-to-market team."
            className="mt-6 max-w-4xl text-5xl font-semibold tracking-tighter text-ink md:text-7xl lg:text-8xl lg:leading-[0.95]"
          />
          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-ink/70 md:text-xl">
            Multi-agent research across the open web, layered reasoning for ICP and positioning, and a polished strategy
            doc — with a user-approved master plan before a single sub-agent runs.
          </p>
          <div className="mt-10 flex flex-wrap gap-3">
            <Link
              href="/login"
              className="inline-flex items-center justify-center rounded-lg bg-slate px-6 py-3 text-sm font-semibold text-cream shadow-glow transition-opacity hover:opacity-90"
            >
              Start free
            </Link>
            <Link
              href="/how-it-works"
              className="inline-flex items-center justify-center rounded-lg border border-mist bg-cream/80 px-6 py-3 text-sm font-semibold text-ink transition-colors hover:border-slate/50"
            >
              How it works
            </Link>
          </div>
          <p className="mt-10 font-mono text-xs text-ink/50">Trusted by founders who ship fast.</p>
        </div>
      </section>

      <Marquee items={sources} />

      <section className="mx-auto max-w-6xl px-4 py-20 md:px-6 md:py-28">
        <RevealOnScroll>
          <SectionHeader
            eyebrow="Three layers"
            title="Research, reason, write — with approvals at every step."
            lead="Sub-agents plan and execute. Parents review. The main agent gates each layer. You approve the master plan first."
          />
        </RevealOnScroll>
        <div className="mt-14 grid gap-6 md:grid-cols-3">
          <RevealOnScroll delay={0.05}>
            <FeatureCard
              icon={Radar}
              title="Research"
              description="Reddit, X, web, and competitor signals — chosen autonomously based on your product context."
            />
          </RevealOnScroll>
          <RevealOnScroll delay={0.1}>
            <FeatureCard
              icon={BookOpen}
              title="Reasoning"
              description="ICP, personas, positioning, and channel ranking synthesized from the research bundle."
            />
          </RevealOnScroll>
          <RevealOnScroll delay={0.15}>
            <FeatureCard
              icon={PenLine}
              title="Writing"
              description="A founder-ready GTM narrative with Markdown and PDF export when the pipeline completes."
            />
          </RevealOnScroll>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-12 md:px-6 md:py-16">
        <RevealOnScroll>
          <LiveActivityDemo />
        </RevealOnScroll>
      </section>

      <section className="mx-auto grid max-w-6xl gap-12 px-4 py-16 md:grid-cols-2 md:px-6 md:py-24">
        <RevealOnScroll>
          <SectionHeader
            eyebrow="Hierarchy"
            title="Plans, Redis memory, and retries — not a black box."
            lead="When a layer misses the bar, the main agent issues revised instructions and the layer retries. LangSmith traces correlate with every run."
          />
        </RevealOnScroll>
        <RevealOnScroll delay={0.08}>
          <AgentHierarchyDiagram />
        </RevealOnScroll>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16 md:px-6 md:py-24">
        <RevealOnScroll>
          <SectionHeader
            eyebrow="Output"
            title="What you get back"
            lead="A structured GTM document you can share with investors, GTM hires, or your own backlog."
          />
        </RevealOnScroll>
        <div className="mt-10 max-w-3xl">
          <RevealOnScroll delay={0.06}>
            <ReportPreviewCard />
          </RevealOnScroll>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-12 md:px-6">
        <div className="grid gap-6 md:grid-cols-3">
          {[
            { k: "200+", v: "Signals per run", d: "Web + social + competitor context" },
            { k: "3", v: "Layer reviews", d: "Research, reasoning, writing gates" },
            { k: "1", v: "Trace per pipeline", d: "LangSmith correlation baked in" },
          ].map((s) => (
            <RevealOnScroll key={s.k}>
              <div className="rounded-2xl border border-mist bg-cream/90 p-6">
                <p className="font-mono text-3xl font-semibold text-ink">{s.k}</p>
                <p className="mt-2 text-lg font-medium text-ink">{s.v}</p>
                <p className="mt-1 text-sm text-ink/65">{s.d}</p>
              </div>
            </RevealOnScroll>
          ))}
        </div>
      </section>

      <section className="mt-12 border-y border-mist bg-ink px-4 py-16 text-cream md:px-6 md:py-20">
        <div className="mx-auto flex max-w-6xl flex-col gap-8 md:flex-row md:items-end md:justify-between">
          <div className="max-w-xl">
            <p className="font-mono text-xs uppercase tracking-[0.25em] text-cream/60">Ready</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight md:text-4xl">Run your first GTM pipeline</h2>
            <p className="mt-3 text-sm leading-relaxed text-cream/75">
              Magic link sign-in. Approve the master plan. Watch the agents work.
            </p>
          </div>
          <EmailCta />
        </div>
      </section>
    </>
  );
}
