"use client";

import Link from "next/link";
import { AnimatedHeadline } from "@/components/marketing/AnimatedHeadline";
import { EmailCta } from "@/components/marketing/EmailCta";
import { HeroDashboardOrbit } from "@/components/marketing/HeroDashboardOrbit";
import { LiveActivityDemo } from "@/components/marketing/LiveActivityDemo";
import { Marquee } from "@/components/marketing/Marquee";
import { RadialOrbitalTimeline } from "@/components/marketing/RadialOrbitalTimeline";
import { ReportPreviewCard } from "@/components/marketing/ReportPreviewCard";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { SectionHeader } from "@/components/marketing/SectionHeader";
import { ParticleField } from "@/components/marketing/ParticleField";
import { AnimatedCounter } from "@/components/marketing/AnimatedCounter";
import { BRAND_NAME, BRAND_SUBHEAD, BRAND_TAGLINE } from "@/lib/brand";
import { ArrowRight } from "lucide-react";

const marqueeItems = [
  "SYS_LATENCY: 180MS",
  "THRUST_FACTOR: 98%",
  "COMPILATION: OK",
  "TRAFFIC_LOOPS: COMPILED",
  "Blueprints compiled",
  "Zero backend leak",
  "Self-hosted docs ready",
  "STOA_ENGINE_ACTIVE",
];

const metrics = [
  { k: 180, s: "ms", v: "SYS.LATENCY", d: "Strategy synthesis happens in milliseconds, not months." },
  { k: 100, s: "%", v: "CONTEXT.DEPTH", d: "Full workspace ingestion depth covers every competitor signal." },
  { k: 98, s: "%", v: "ENGINE.THRUST", d: "Conversion probability verified across organic distribution paths." },
];

export default function LandingPage() {
  return (
    <>
      <section className="relative overflow-hidden px-4 pb-20 pt-10 md:px-6 md:pb-28 md:pt-16">
        <ParticleField />
        <div className="container-page relative">
          <div className="grid gap-12 lg:grid-cols-[1.04fr_0.96fr] lg:items-center">
            <div>
              <div className="inline-flex items-center gap-2 border border-primary/30 bg-primary/5 px-3 py-1 font-mono">
                <span className="h-1.5 w-1.5 bg-primary animate-pulse" />
                <p className="text-[10px] uppercase font-bold tracking-widest text-primary">{BRAND_NAME}_SYSTEM_LOADED</p>
              </div>
              <AnimatedHeadline
                text={BRAND_TAGLINE}
                className="mt-7 max-w-5xl font-display text-4xl font-extrabold leading-[1.05] tracking-tight text-on-surface md:text-6xl lg:text-7xl uppercase"
              />
              <p className="mt-6 max-w-2xl text-base leading-relaxed text-on-surface-variant font-mono">
                {BRAND_SUBHEAD}
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                <Link href="/waitlist" className="btn-primary px-6 py-3 text-center text-sm font-mono tracking-wider uppercase">
                  RUN_GET_STARTED.SH <ArrowRight className="ml-2 inline h-4 w-4" />
                </Link>
                <Link href="/see-it-in-action" className="btn-secondary px-6 py-3 text-center text-sm font-mono uppercase">
                  [SEE_IT_IN_ACTION]
                </Link>
              </div>
              
              {/* Copyable Quickstart Command */}
              <div className="mt-8 font-mono text-xs text-on-surface-variant flex items-center gap-2 select-all border border-outline-variant/60 bg-surface-dim/40 px-3.5 py-2.5 max-w-xs">
                <span className="text-primary font-bold">$</span>
                <span>npx create-stoa-app@latest</span>
              </div>

              <div className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-xs text-on-surface-variant font-mono">
                {["[✔] Strategy compiled", "[✔] Zero data leak", "[✔] Code-ready campaigns"].map((item) => (
                  <span key={item} className="inline-flex items-center gap-2">
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
            lead={BRAND_SUBHEAD}
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
              lead="Every campaign stays tied to the same strategy blueprint, brand voice, and company context—without switching tools."
            />
          </RevealOnScroll>
          <RevealOnScroll delay={0.06}>
            <ReportPreviewCard />
          </RevealOnScroll>
        </div>
      </section>

      <section className="container-page py-12 md:py-16">
        <div className="grid gap-6 md:grid-cols-3">
          {metrics.map((s, i) => (
            <RevealOnScroll key={s.v} delay={i * 0.08}>
              <div className="border border-outline-variant p-6 bg-surface-container-lowest flex flex-col justify-between h-full font-mono">
                <div>
                  <span className="text-[10px] text-secondary font-bold uppercase tracking-widest block mb-2">[{i + 1}] {s.v}</span>
                  <p className="font-display text-4xl font-extrabold tracking-tight text-primary mt-1">
                    <AnimatedCounter value={s.k} suffix={s.s} />
                  </p>
                </div>
                <p className="mt-4 text-xs leading-relaxed text-on-surface-variant">{s.d}</p>
              </div>
            </RevealOnScroll>
          ))}
        </div>
      </section>

      <section className="container-page mt-12 pb-16">
        <div className="relative overflow-hidden border border-outline-variant bg-surface-container-lowest px-6 py-14 text-on-surface md:px-10 md:py-16">
          <ParticleField />
          <div className="absolute right-0 top-0 h-80 w-80 translate-x-1/3 -translate-y-1/3 rounded-full bg-primary/10 blur-3xl" />
          <div className="relative flex flex-col gap-8 md:flex-row md:items-end md:justify-between">
            <div className="max-w-2xl font-mono">
              <span className="text-[10px] text-primary font-bold uppercase tracking-wider">[LOAD_DEPLOYMENT]</span>
              <h2 className="mt-4 font-display text-3xl font-bold tracking-tight text-on-surface uppercase">Build your first company workspace.</h2>
              <p className="mt-4 text-xs leading-relaxed text-on-surface-variant">{BRAND_SUBHEAD}</p>
            </div>
            <EmailCta />
          </div>
        </div>
      </section>
    </>
  );
}
