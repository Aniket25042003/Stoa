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
import { ArrowRight, BookOpen, CheckCircle2, PenLine, Radar, Sparkles } from "lucide-react";

const sources = ["Crawler", "Tavily", "Jina", "SerpAPI", "LangSmith", "Supabase", "Redis"];

const metrics = [
  { k: "200+", v: "Signals per run", d: "Web, social, and competitor context" },
  { k: "3", v: "Review layers", d: "Research, reasoning, and writing gates" },
  { k: "1", v: "Trace per pipeline", d: "LangSmith correlation baked in" },
];

export default function LandingPage() {
  return (
    <>
      <section className="relative overflow-hidden px-4 pb-20 pt-10 md:px-6 md:pb-28 md:pt-16">
        <GradientOrb />
        <div className="container-page relative">
          <div className="grid gap-12 lg:grid-cols-[1.04fr_0.96fr] lg:items-center">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-white/62 px-3 py-2 shadow-soft backdrop-blur-md">
                <Sparkles className="h-3.5 w-3.5 text-primary" />
                <p className="eyebrow text-[11px]">High-performance GTM automation</p>
              </div>
              <AnimatedHeadline
                text="Your autonomous go-to-market command center."
                className="mt-7 max-w-5xl font-display text-5xl font-extrabold leading-[1.02] tracking-[-0.055em] text-slate-deep md:text-7xl lg:text-8xl"
              />
              <p className="mt-7 max-w-2xl text-lg leading-8 text-on-surface-variant md:text-xl">
                Multi-agent research, layered strategic reasoning, and polished GTM reports - with a user-approved master plan before any agent executes.
              </p>
              <div className="mt-10 flex flex-wrap gap-3">
                <Link href="/login" className="btn-primary px-6 py-3 text-sm">
                  Start free <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
                <Link href="/how-it-works" className="btn-secondary px-6 py-3 text-sm">
                  See workflow
                </Link>
              </div>
              <div className="mt-10 flex flex-wrap gap-4 text-sm text-on-surface-variant">
                {["Plan approval", "Live SSE activity", "PDF-ready output"].map((item) => (
                  <span key={item} className="inline-flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-primary" />
                    {item}
                  </span>
                ))}
              </div>
            </div>

            <div className="relative">
              <div className="absolute -inset-6 rounded-[2rem] bg-gradient-to-br from-primary/20 via-violet-pulse/10 to-transparent blur-2xl" />
              <div className="relative overflow-hidden rounded-[2rem] border border-white/70 bg-slate-deep p-5 text-white shadow-card">
                <div className="absolute inset-0 opacity-30 [background-image:linear-gradient(to_right,rgb(255_255_255_/_0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgb(255_255_255_/_0.08)_1px,transparent_1px)] [background-size:32px_32px]" />
                <div className="relative flex items-center justify-between gap-4 border-b border-white/10 pb-4">
                  <div>
                    <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-inverse-primary">Pipeline health</p>
                    <p className="mt-1 font-display text-2xl font-bold tracking-[-0.03em]">GTM run active</p>
                  </div>
                  <span className="rounded-full bg-white/10 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.14em] text-white/80">Live</span>
                </div>
                <div className="relative mt-5 grid gap-3">
                  {[
                    ["Research", "Competitor SERP mapping", "86%"],
                    ["Reasoning", "ICP and channel scoring", "68%"],
                    ["Writing", "Narrative assembly", "41%"],
                  ].map(([phase, detail, progress]) => (
                    <div key={phase} className="rounded-2xl border border-white/10 bg-white/8 p-4 backdrop-blur-md">
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <p className="font-display text-sm font-bold">{phase}</p>
                          <p className="mt-1 text-xs text-white/58">{detail}</p>
                        </div>
                        <p className="font-mono text-xs text-inverse-primary">{progress}</p>
                      </div>
                      <div className="mt-3 h-1 overflow-hidden rounded-full bg-white/10">
                        <div className="h-full animate-shimmer rounded-full progress-shimmer" style={{ width: progress }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <Marquee items={sources} />

      <section className="container-page py-20 md:py-28">
        <RevealOnScroll>
          <SectionHeader
            eyebrow="Three layers"
            title="Research, reason, write - with approvals at every step."
            lead="Sub-agents plan and execute. Parents review. The main agent gates each layer. You approve the master plan first."
          />
        </RevealOnScroll>
        <div className="mt-14 grid gap-6 md:grid-cols-3">
          <RevealOnScroll delay={0.05}>
            <FeatureCard icon={Radar} title="Research" description="Web search, crawler passes, and competitor signals selected based on product context." />
          </RevealOnScroll>
          <RevealOnScroll delay={0.1}>
            <FeatureCard icon={BookOpen} title="Reasoning" description="ICP, personas, positioning, and channel ranking synthesized from the research bundle." />
          </RevealOnScroll>
          <RevealOnScroll delay={0.15}>
            <FeatureCard icon={PenLine} title="Writing" description="A founder-ready GTM narrative with Markdown and PDF export when the pipeline completes." />
          </RevealOnScroll>
        </div>
      </section>

      <section className="container-page py-12 md:py-16">
        <RevealOnScroll>
          <LiveActivityDemo />
        </RevealOnScroll>
      </section>

      <section className="container-page grid gap-12 py-16 md:grid-cols-2 md:py-24 md:items-center">
        <RevealOnScroll>
          <SectionHeader
            eyebrow="Hierarchy"
            title="Plans, memory, and retries - not a black box."
            lead="When a layer misses the bar, the main agent issues revised instructions and the layer retries. LangSmith traces correlate with every run."
          />
        </RevealOnScroll>
        <RevealOnScroll delay={0.08}>
          <AgentHierarchyDiagram />
        </RevealOnScroll>
      </section>

      <section className="container-page py-16 md:py-24">
        <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          <RevealOnScroll>
            <SectionHeader
              eyebrow="Output"
              title="A GTM document your team can act on."
              lead="Share strategy with investors, GTM hires, or your backlog without losing the source trail behind each recommendation."
            />
          </RevealOnScroll>
          <RevealOnScroll delay={0.06}>
            <ReportPreviewCard />
          </RevealOnScroll>
        </div>
      </section>

      <section className="container-page py-12 md:py-16">
        <div className="grid gap-6 md:grid-cols-3">
          {metrics.map((s) => (
            <RevealOnScroll key={s.k}>
              <div className="rounded-3xl p-7 card-glass">
                <p className="font-display text-5xl font-extrabold tracking-[-0.05em] gradient-text">{s.k}</p>
                <p className="mt-3 font-display text-xl font-bold text-slate-deep">{s.v}</p>
                <p className="mt-2 text-sm leading-6 text-on-surface-variant">{s.d}</p>
              </div>
            </RevealOnScroll>
          ))}
        </div>
      </section>

      <section className="container-page mt-12">
        <div className="relative overflow-hidden rounded-[2rem] bg-slate-deep px-6 py-14 text-white shadow-card md:px-10 md:py-16">
          <div className="absolute right-0 top-0 h-80 w-80 translate-x-1/3 -translate-y-1/3 rounded-full bg-violet-pulse/30 blur-3xl" />
          <div className="relative flex flex-col gap-8 md:flex-row md:items-end md:justify-between">
            <div className="max-w-2xl">
              <p className="eyebrow text-inverse-primary">Ready</p>
              <h2 className="mt-4 font-display text-4xl font-bold tracking-[-0.04em] md:text-5xl">Run your first GTM pipeline</h2>
              <p className="mt-4 text-sm leading-7 text-white/68">Google sign-in. Approve the master plan. Watch the agents work.</p>
            </div>
            <EmailCta />
          </div>
        </div>
      </section>
    </>
  );
}
