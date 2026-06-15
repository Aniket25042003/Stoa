import { BRAND_SUBHEAD, BRAND_TAGLINE } from "@/lib/brand";

export type LandingSectionKind = "hero" | "feature" | "cta";

/** Corner placement for scrollytelling feature cards around the 3D centerpiece */
export type TextAnchor =
  | "top-left"
  | "top-right"
  | "middle-left"
  | "middle-right"
  | "bottom-left"
  | "bottom-right";

export interface LandingSection {
  id: string;
  kind: LandingSectionKind;
  eyebrow: string;
  title: string;
  description: string;
  chapter?: string;
  /** Scroll chapter index (features only) */
  faceIndex?: number;
  /** Where the card appears around the centered 3D object */
  textAnchor?: TextAnchor;
}

export const LANDING_SECTIONS: LandingSection[] = [
  {
    id: "hero",
    kind: "hero",
    eyebrow: "Marketing Intelligence",
    title: BRAND_TAGLINE,
    description: BRAND_SUBHEAD,
    textAnchor: "top-left",
  },
  {
    id: "icp-research",
    kind: "feature",
    eyebrow: "Customer Intelligence",
    title: "ICP & Customer Research",
    description:
      "Turn CRM, calls, and feedback into a living ICP",
    chapter: "01",
    faceIndex: 0,
    textAnchor: "top-left",
  },
  {
    id: "content-bottleneck",
    kind: "feature",
    eyebrow: "Content Velocity",
    title: "Content Creation Bottleneck",
    description:
      "From signals to briefs and assets - stop starting every campaign from a blank page.",
    chapter: "02",
    faceIndex: 1,
    textAnchor: "top-right",
  },
  {
    id: "competitive-intel",
    kind: "feature",
    eyebrow: "Market Radar",
    title: "Competitive Intelligence",
    description:
      "Surface competitor moves and positioning shifts before they become noise.",
    chapter: "03",
    faceIndex: 2,
    textAnchor: "middle-left",
  },
  {
    id: "campaign-analysis",
    kind: "feature",
    eyebrow: "Performance",
    title: "Campaign Analysis",
    description:
      "See what worked and why, backed by stored evidence - not another dashboard rabbit hole.",
    chapter: "04",
    faceIndex: 3,
    textAnchor: "middle-right",
  },
  {
    id: "sales-marketing-align",
    kind: "feature",
    eyebrow: "GTM Alignment",
    title: "Sales–Marketing Alignment",
    description:
      "One intelligence layer both teams trust — same ICP, same proof, same story.",
    chapter: "05",
    faceIndex: 4,
    textAnchor: "bottom-left",
  },
  {
    id: "launch-orchestration",
    kind: "feature",
    eyebrow: "Orchestration",
    title: "Campaign Launch Orchestration",
    description:
      "Strategy → briefs → creative → launch - connected in one workspace.",
    chapter: "06",
    faceIndex: 5,
    textAnchor: "bottom-right",
  },
  {
    id: "waitlist",
    kind: "cta",
    eyebrow: "Early Access",
    title: "Join the waitlist",
    description: "Be first to try Stoa. Early access is opening soon.",
  },
];

/** Hero section (no 3D stage) */
export const HERO_SECTION = LANDING_SECTIONS[0];

/** 6 features — drives scroll-linked 3D stage */
export const FEATURE_SCROLL_SECTIONS = LANDING_SECTIONS.filter((s) => s.kind === "feature");

export const FEATURE_SECTION_COUNT = 6;

/** Orb face textures — 1:1 with FEATURE_SCROLL_SECTIONS order */
export const ORB_FACE_IMAGES = [
  "/images/marketing/orb-faces/01-icp-research.webp",
  "/images/marketing/orb-faces/02-content-bottleneck.webp",
  "/images/marketing/orb-faces/03-competitive-intel.webp",
  "/images/marketing/orb-faces/04-campaign-analysis.webp",
  "/images/marketing/orb-faces/05-gtm-alignment.webp",
  "/images/marketing/orb-faces/06-launch-orchestration.webp",
] as const;

/** Self-hosted studio HDRI for orb IBL (CSP-safe; do not use drei CDN presets). */
export const ORB_ENVIRONMENT_HDR = "/images/marketing/hdri/studio_small_03_1k.hdr";

/** Fallback poster when WebGL is unavailable */
export const CORE_FALLBACK_POSTER = "/images/marketing/orb-faces/orb-fallback.webp";

export const TEXT_ANCHOR_CLASSES: Record<TextAnchor, string> = {
  "top-left": "top-[10%] left-[5%] max-w-[min(300px,38vw)] text-left items-start",
  "top-right": "top-[10%] right-[5%] max-w-[min(300px,38vw)] text-right items-end",
  "middle-left": "top-1/2 -translate-y-1/2 left-[5%] max-w-[min(300px,38vw)] text-left items-start",
  "middle-right": "top-1/2 -translate-y-1/2 right-[5%] max-w-[min(300px,38vw)] text-right items-end",
  "bottom-left": "bottom-[12%] left-[5%] max-w-[min(300px,38vw)] text-left items-start",
  "bottom-right": "bottom-[12%] right-[5%] max-w-[min(300px,38vw)] text-right items-end",
};
