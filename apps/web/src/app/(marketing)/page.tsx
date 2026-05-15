"use client";

import Link from "next/link";
import { AnimatedHeadline } from "@/components/marketing/AnimatedHeadline";
import { EmailCta } from "@/components/marketing/EmailCta";
import { GradientOrb } from "@/components/marketing/GradientOrb";
import { HeroDashboardOrbit } from "@/components/marketing/HeroDashboardOrbit";
import { LiveActivityDemo } from "@/components/marketing/LiveActivityDemo";
import { Marquee } from "@/components/marketing/Marquee";
import { RadialOrbitalTimeline } from "@/components/marketing/RadialOrbitalTimeline";
import { ReportPreviewCard } from "@/components/marketing/ReportPreviewCard";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { SectionHeader } from "@/components/marketing/SectionHeader";
import { ArrowRight, CheckCircle2, Sparkles } from "lucide-react";

const marqueeItems = [
  "Company-scoped workspaces",
  "GTM plans you can edit",
  "Marketing ideas and campaign assets",
  "Brand voice that stays consistent",
  "Strategy and creative in one place",
  "Multiple companies, separate context",
  "Launch-ready next steps",
];

const metrics = [
  { k: "2", v: "Focused workspaces", d: "GTM planning and marketing execution side by side" },
  { k: "Many", v: "Company memories", d: "Each company keeps its own strategy, voice, and assets" },
  { k: "1", v: "Command center", d: "Dashboard, GTM, and Marketing stay connected" },
];

export default function LandingPage() {
  return (
    <>
      <section className="relative overflow-hidden px-4 pb-20 pt-10 md:px-6 md:pb-28 md:pt-16">
        <GradientOrb />
        <div className="container-page relative">
          <div className="grid gap-12 lg:grid-cols-[1.04fr_0.96fr] lg:items-center">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-surface-container-low/70 px-3 py-2 shadow-soft backdrop-blur-md">
                <Sparkles className="h-3.5 w-3.5 text-primary" />
                <p className="eyebrow text-[11px]">Strategy and marketing workspace</p>
              </div>
              <AnimatedHeadline
                text="One command center for GTM and marketing."
                className="mt-7 max-w-5xl font-display text-5xl font-extrabold leading-[1.02] tracking-[-0.055em] text-on-surface md:text-7xl lg:text-8xl"
              />
              <p className="mt-7 max-w-2xl text-lg leading-8 text-on-surface-variant md:text-xl">
                nexara helps you shape company strategy, build editable GTM plans, and turn marketing ideas into campaign-ready copy, scripts, and creative direction.
              </p>
              <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                <Link href="/login" className="btn-primary px-6 py-3 text-center text-sm sm:inline-flex sm:items-center sm:justify-center">
                  Start free <ArrowRight className="ml-2 inline h-4 w-4" />
                </Link>
                <Link href="/how-it-works" className="btn-secondary px-6 py-3 text-center text-sm">
                  See how it works
                </Link>
              </div>
              <div className="mt-10 flex flex-wrap gap-x-4 gap-y-2 text-sm text-on-surface-variant">
                {["GTM planning", "Marketing execution", "Company memory"].map((item) => (
                  <span key={item} className="inline-flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-primary" />
                    {item}
                  </span>
                ))}
              </div>
            </div>

            <HeroDashboardOrbit />
          </div>
        </div>
      </section>

      <Marquee items={marqueeItems} />

      <section className="container-page py-20 md:py-28">
        <RevealOnScroll>
          <SectionHeader
            eyebrow="Connected workspace"
            title="Strategy and creative stay in sync."
            lead="Start with company context, build a GTM plan, then keep marketing work aligned with the same positioning and brand voice."
          />
        </RevealOnScroll>
        <RevealOnScroll delay={0.05}>
          <div className="mt-14">
            <RadialOrbitalTimeline />
          </div>
        </RevealOnScroll>
      </section>

      <section className="container-page py-12 md:py-16">
        <RevealOnScroll>
          <LiveActivityDemo />
        </RevealOnScroll>
      </section>

      <section className="container-page py-16 md:py-24">
        <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          <RevealOnScroll>
            <SectionHeader
              eyebrow="Output"
              title="Plans, briefs, copy, scripts, and assets your team can use."
              lead="Keep strategy and marketing execution together so each campaign reflects the company you are building."
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
                <p className="mt-3 font-display text-xl font-bold text-on-surface">{s.v}</p>
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
              <h2 className="mt-4 font-display text-4xl font-bold tracking-[-0.04em] md:text-5xl">Build your first company workspace.</h2>
              <p className="mt-4 text-sm leading-7 text-white/68">Sign in, add your company details, and start planning GTM and marketing from one place.</p>
            </div>
            <EmailCta />
          </div>
        </div>
      </section>
    </>
  );
}
