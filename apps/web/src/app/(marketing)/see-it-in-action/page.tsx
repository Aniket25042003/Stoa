"use client";

import { MarketingCtaBand } from "@/components/marketing/MarketingCtaBand";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { SectionHeader } from "@/components/marketing/SectionHeader";
import {
  SeeItInActionWalkthrough,
  type WalkthroughStep,
} from "@/components/marketing/SeeItInActionWalkthrough";
import { MarketingPageShell } from "@/components/marketing/immersive/MarketingPageShell";
import { BRAND_SUBHEAD, BRAND_TAGLINE } from "@/lib/brand";

const steps: WalkthroughStep[] = [
  {
    module: "Intake",
    title: "Tell us about your company",
    body: "Add the basics once: who you serve, what you sell, and the goals you want to conquer next.",
    detail:
      "Stoa normalizes your company brief into a structured brand profile - audience segments, category, motion stage, and near-term GTM goals, so every downstream workflow starts from the same source of truth.",
    inputs: ["Company brief", "ICP notes", "Product positioning"],
    outputs: ["Brand profile index", "Audience segment map", "Goal priority stack"],
    logs: [
      "SYS · Booting intake node…",
      "INGEST · Parsing company brief & profile…",
      "INGEST · Extracting ICP: technical founders, 10–200 employees.",
      "INGEST · Category tagged: B2B dev-tools · motion: product-led.",
      "INGEST · Goals ranked: awareness → activation → expansion.",
      "STATUS · Brand profile compiled and indexed.",
    ],
  },
  {
    module: "Strategy",
    title: "Get a strategy that fits",
    body: "Start from a custom strategy blueprint built for your unique market angle, then refine it as your product grows.",
    detail:
      "The strategy compiler evaluates channel fit against your profile, scores organic and paid paths, and assembles a blueprint you can edit positioning angles, channel mix, and launch sequencing included.",
    inputs: ["Brand profile", "Market category signals", "Competitive context"],
    outputs: ["Strategy blueprint", "Channel priority matrix", "Positioning angles"],
    logs: [
      "SYS · Scanning market routing options…",
      "ROUTER · Evaluated 18 acquisition channels.",
      "ROUTER · Scoring: community 0.91 · content 0.87 · paid 0.62.",
      "ROUTER · Selected: github/showcase, hn/launch, eng_blogs.",
      "ROUTER · Blueprint sections: narrative, channels, milestones.",
      "STATUS · Strategy blueprint compiled successfully.",
    ],
  },
  {
    module: "Workspace",
    title: "Refine through conversation",
    body: "Explore directions, query positioning ideas, or request channel suggestions in your strategy workspace.",
    detail:
      "Ask follow-up questions - challenge assumptions, stress-test messaging, or request alternate channel mixes. Responses stay grounded in your indexed profile and strategy blueprint.",
    inputs: ["Strategy blueprint", "Conversation prompts", "Revision constraints"],
    outputs: ["Refined positioning", "Channel alternatives", "Decision log"],
    logs: [
      "SYS · Opening context workspace stream…",
      "STREAM · Loading profile + blueprint into session context.",
      "STREAM · Retrieval: 12 evidence chunks from brand index.",
      "STREAM · Tuning parameters: temperature=0.15, cost=optimal.",
      "STREAM · Ready for iterative strategy queries.",
      "STATUS · Interactive workspace stream active.",
    ],
  },
  {
    module: "Creative",
    title: "Set your creative direction",
    body: "Establish brand voice parameters, visual style preferences, and creative constraints to guide campaign outputs.",
    detail:
      "Voice, tone, visual references, and do/don't rules are compiled into creative guidelines so campaign assets stay on-brand without re-briefing every time.",
    inputs: ["Brand voice notes", "Visual references", "Tone constraints"],
    outputs: ["Creative direction doc", "Voice parameters", "Layout guardrails"],
    logs: [
      "SYS · Loading creative guideline compiler…",
      "COMPILE · Tone: technical, minimalist, hyper-efficient.",
      "COMPILE · Voice axes: clarity=high · jargon=low · warmth=med.",
      "COMPILE · Visual: sharp grid, indigo accent, high contrast.",
      "COMPILE · Constraints locked for downstream generation.",
      "STATUS · Creative direction guidelines validated.",
    ],
  },
  {
    module: "Campaigns",
    title: "Create campaigns that land",
    body: "Generate high-conversion campaign copy, structured creative briefs, script drafts, and custom distribution schedules.",
    detail:
      "Campaign generation pulls from strategy, creative direction, and customer signals to produce channel-ready copy, briefs, scripts, and a distribution calendar - all traceable to source context.",
    inputs: ["Strategy blueprint", "Creative guidelines", "Launch objective"],
    outputs: ["Campaign copy pack", "Creative briefs", "Distribution schedule"],
    logs: [
      "SYS · Generating launch-ready campaign templates…",
      "BUILD · Angle: open-core transparency · hook strength 0.92.",
      "BUILD · Assets: landing copy, email sequence, social set.",
      "BUILD · Briefs: hero video, founder thread, launch post.",
      "BUILD · Calendar: 3-week organic thrust mapped.",
      "STATUS · Launch assets synthesized.",
    ],
  },
  {
    module: "Portfolio",
    title: "Scale across brands",
    body: "Stoa keeps workspaces and contexts separate so you can easily manage a portfolio of distinct brands.",
    detail:
      "Each brand gets an isolated workspace - separate profiles, strategies, conversations, and campaign assets. Switch context without cross-contamination across your portfolio.",
    inputs: ["New brand brief", "Tenant isolation rules", "Team permissions"],
    outputs: ["Isolated workspace", "Scoped context index", "Portfolio switcher"],
    logs: [
      "SYS · Multiplexing brand contexts…",
      "ISOLATION · Provisioning workspace tenant #4.",
      "ISOLATION · Context boundary: profile, strategy, campaigns.",
      "ISOLATION · Cross-tenant retrieval blocked · audit logged.",
      "ISOLATION · Team roles scoped to active workspace.",
      "STATUS · Separate tenant workspaces online.",
    ],
  },
];

const atAGlance = [
  "Secure sign-in",
  "Separate context for every brand",
  "Strategy blueprints & campaign drafts",
  "Unified brand voice continuity",
  "Clean separate workspaces",
];

export default function SeeItInActionPage() {
  return (
    <MarketingPageShell>
      <RevealOnScroll>
        <SectionHeader
          eyebrow="The Stoa way"
          title="From brand context to strategy and campaign execution."
          lead={`${BRAND_TAGLINE} ${BRAND_SUBHEAD}`}
        />
      </RevealOnScroll>

      <SeeItInActionWalkthrough steps={steps} atAGlance={atAGlance} />

      <RevealOnScroll>
        <MarketingCtaBand
          className="mt-20"
          eyebrow="Ready to deploy"
          title="Try it now"
          description={BRAND_SUBHEAD}
          ctaLabel="Join the waitlist"
          ctaHref="/waitlist"
        />
      </RevealOnScroll>
    </MarketingPageShell>
  );
}
