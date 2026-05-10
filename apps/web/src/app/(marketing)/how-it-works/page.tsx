import Link from "next/link";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { SectionHeader } from "@/components/marketing/SectionHeader";

const steps = [
  {
    title: "Founder input",
    body: "You describe the product, stage, constraints, and horizon. That context seeds the main agent's master plan - nothing executes until you approve it.",
  },
  {
    title: "Master plan approval",
    body: "The draft plan is yours to edit. Request changes in natural language; the main agent regenerates until you approve the top-level operating plan.",
  },
  {
    title: "Research layer",
    body: "The research parent plans steps, calls sub-agents for search and crawl work, stores observations, and seeks approval from the main agent.",
  },
  {
    title: "Reasoning layer",
    body: "Segmentation, positioning, and channel strategy synthesize the evidence bundle. Gaps become concrete revision instructions instead of vague failures.",
  },
  {
    title: "Writing layer",
    body: "The writer turns approved reasoning into a crisp GTM document - Markdown first, PDF export from the API when the run completes.",
  },
  {
    title: "Report + traces",
    body: "SSE keeps the UI honest about what's running. LangSmith trace IDs ride along events so regressions can be debugged without guessing.",
  },
];

export default function HowItWorksPage() {
  return (
    <div className="container-page py-16 md:py-24">
      <RevealOnScroll>
        <SectionHeader
          eyebrow="Pipeline"
          title="From prompt to GTM doc, with gates you can trust."
          lead="Autonomy where it helps, approvals where it matters - you, then the main agent, then parents, then sub-agents."
        />
      </RevealOnScroll>

      <div className="mt-10 rounded-3xl p-5 font-mono text-xs leading-7 text-on-surface-variant card-glass lg:hidden">
        <p className="text-primary">Stack</p>
        <p className="mt-2">Next.js | Supabase | FastAPI | Celery | LangGraph | Redis | MCP | LangSmith</p>
      </div>

      <div className="mt-16 lg:grid lg:grid-cols-[0.9fr_1.1fr] lg:gap-16">
        <aside className="relative mb-12 lg:mb-0">
          <div className="sticky top-28 hidden overflow-hidden rounded-3xl bg-slate-deep p-8 font-mono text-xs leading-7 text-white/72 shadow-card lg:block">
            <div className="absolute inset-0 opacity-25 [background-image:linear-gradient(to_right,rgb(255_255_255_/_0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgb(255_255_255_/_0.08)_1px,transparent_1px)] [background-size:36px_36px]" />
            <div className="relative">
              <p className="text-inverse-primary">Stack</p>
              <ul className="mt-4 space-y-3">
                <li>Next.js + Supabase auth</li>
                <li>FastAPI + Celery workers</li>
                <li>LangGraph orchestration</li>
                <li>Redis shared memory</li>
                <li>MCP research tools</li>
                <li>LangSmith tracing</li>
              </ul>
              <p className="mt-8 text-inverse-primary">Flow</p>
              <pre className="mt-3 whitespace-pre-wrap text-[11px] text-white/64">
                {`User
  -> approve
Main agent
  -> instruct
Research -> Reasoning -> Writing
  ->
GTM report + PDF`}
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
          <p className="mt-2 text-sm text-on-surface-variant">Sign in, create a run, approve the plan, and watch the pipeline.</p>
          <Link href="/login" className="btn-primary mt-6 px-6 py-3 text-sm">
            Get started
          </Link>
        </div>
      </RevealOnScroll>
    </div>
  );
}
