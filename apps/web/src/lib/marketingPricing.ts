export type PricingTier = {
  name: string;
  price: string;
  period: string;
  description: string;
  features: string[];
  cta: string;
  href: string;
  highlighted: boolean;
};

export const PRICING_COMPARE_ROWS = [
  { label: "Brand workspaces", starter: "1", pro: "5", team: "Unlimited" },
  { label: "Strategy blueprinting", starter: "yes", pro: "yes", team: "yes" },
  { label: "Campaign deliverables", starter: "Limited", pro: "yes", team: "yes" },
  { label: "Export-ready documents", starter: "no", pro: "yes", team: "yes" },
] as const;

export function getPricingTiers(yearly: boolean, authEntry: string): PricingTier[] {
  return [
    {
      name: "Starter",
      price: "$0",
      period: yearly ? "/ year" : "/ month",
      description: "For founders mapping their first product narrative.",
      features: ["1 brand workspace", "Strategy blueprint", "Campaign ideation", "Community access"],
      cta: "Start free",
      href: authEntry,
      highlighted: false,
    },
    {
      name: "Pro",
      price: yearly ? "$190" : "$19",
      period: yearly ? "/ year" : "/ month",
      description: "For growing companies launching dynamic weekly campaigns.",
      features: [
        "5 brand workspaces",
        "Full strategy development",
        "Campaign-ready deliverables",
        "Creative direction tools",
        "Priority support",
      ],
      cta: "Get Pro",
      href: authEntry,
      highlighted: true,
    },
    {
      name: "Team",
      price: yearly ? "$490" : "$49",
      period: yearly ? "/ year" : "/ month",
      description: "For agencies and teams running campaign studios at scale.",
      features: [
        "Unlimited brand workspaces",
        "Shared team dashboard",
        "Priority support",
        "Export-ready documents",
      ],
      cta: "Talk to us",
      href: "#faq",
      highlighted: false,
    },
  ];
}
