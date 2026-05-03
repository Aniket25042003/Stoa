import Link from "next/link";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { SectionHeader } from "@/components/marketing/SectionHeader";

const steps = [
  {
    title: "Founder input",
    body: "You describe the product, stage, constraints, and horizon. That context seeds the main agent’s master plan — nothing executes until you say so.",
  },
  {
    title: "Master plan approval",
    body: "The draft plan is yours to edit. Request changes in natural language; the main agent regenerates until you approve. This is the top gate before Redis-backed agent work begins.",
  },
  {
    title: "Research layer",
    body: "The research parent plans steps, calls sub-agents (web search, Playwright crawl, competitors), stores observations in Redis, and seeks approval from the main agent. Rejections become targeted revision instructions instead of hard stops.",
  },
  {
    title: "Reasoning layer",
    body: "Segmentation, positioning, and channel strategy synthesize the bundle. The main agent reviews completeness and can send the layer back with concrete gaps to close.",
  },
  {
    title: "Writing layer",
    body: "The writer turns approved reasoning into a crisp GTM document — Markdown first, PDF export from the API when the run completes.",
  },
  {
    title: "Report + traces",
    body: "SSE keeps the UI honest about what’s running. LangSmith trace IDs ride along events so you can debug any regression without guessing which LLM call failed.",
  },
];

export default function HowItWorksPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-16 md:px-6 md:py-24">
      <RevealOnScroll>
        <SectionHeader
          eyebrow="Pipeline"
          title="From prompt to GTM doc, with gates you can trust."
          lead="Autonomy where it helps, approvals where it matters — you, then the main agent, then parents, then sub-agents."
        />
      </RevealOnScroll>

      <div className="mt-8 rounded-2xl border border-mist bg-cream/90 p-4 font-mono text-[11px] leading-relaxed text-ink/75 lg:hidden">
        <p className="text-slate">Stack</p>
        <p className="mt-2">Next.js · Supabase · FastAPI · Celery · LangGraph · Redis · MCP · LangSmith</p>
      </div>

      <div className="mt-16 lg:grid lg:grid-cols-2 lg:gap-16">
        <aside className="relative mb-12 lg:mb-0">
          <div className="sticky top-28 hidden rounded-2xl border border-mist bg-cream/95 p-8 font-mono text-xs leading-relaxed text-ink/80 lg:block">
            <p className="text-slate">Stack</p>
            <ul className="mt-4 space-y-3">
              <li>• Next.js + Supabase auth</li>
              <li>• FastAPI + Celery workers</li>
              <li>• LangGraph orchestration</li>
              <li>• Redis shared memory</li>
              <li>• MCP research tools</li>
              <li>• LangSmith tracing</li>
            </ul>
            <p className="mt-8 text-slate">Flow</p>
            <pre className="mt-3 whitespace-pre-wrap text-[11px] text-ink/70">
              {`User
  ↓ approve
Main agent
  ↓ instruct
Research → Reasoning → Writing
  ↓
GTM report + PDF`}
            </pre>
          </div>
        </aside>
        <div className="space-y-16">
          {steps.map((s, i) => (
            <RevealOnScroll key={s.title} delay={0.04 * i}>
              <article className="min-h-[50vh] border-l-2 border-mist pl-6 md:pl-10">
                <p className="font-mono text-xs uppercase tracking-[0.2em] text-slate">
                  Step {String(i + 1).padStart(2, "0")}
                </p>
                <h2 className="mt-3 text-3xl font-semibold tracking-tight text-ink md:text-4xl">{s.title}</h2>
                <p className="mt-4 text-base leading-relaxed text-ink/75 md:text-lg">{s.body}</p>
              </article>
            </RevealOnScroll>
          ))}
        </div>
      </div>

      <RevealOnScroll>
        <div className="mt-20 rounded-2xl border border-mist bg-cream/90 p-8 text-center">
          <p className="text-lg font-medium text-ink">Try it now</p>
          <p className="mt-2 text-sm text-ink/65">Sign in, create a run, approve the plan, and watch the pipeline.</p>
          <Link
            href="/login"
            className="mt-6 inline-flex rounded-lg bg-slate px-6 py-3 text-sm font-semibold text-cream shadow-glow transition-opacity hover:opacity-90"
          >
            Get started
          </Link>
        </div>
      </RevealOnScroll>
    </div>
  );
}
