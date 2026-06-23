import { BRAND_NAME, BRAND_TAGLINE } from "@/lib/brand";

export type FaqCategory = "Product" | "Strategy" | "Marketing" | "Pricing" | "Privacy";

export type MarketingFaq = {
  id: string;
  cat: FaqCategory;
  q: string;
  a: string;
};

export const MARKETING_FAQS: MarketingFaq[] = [
  {
    id: "p1",
    cat: "Product",
    q: `What is ${BRAND_NAME}?`,
    a: `${BRAND_NAME} is a marketing intelligence platform for GTM teams. ${BRAND_TAGLINE} Connect the tools and files you already use, turn customer and market signals into clear insight, and move from answers to campaign-ready output in one workspace.`,
  },
  {
    id: "p2",
    cat: "Product",
    q: "Can I manage more than one company or brand?",
    a: "Yes. Run a separate workspace for each company or brand you support. Switch anytime - each keeps its own profile, connected data, insights, and campaigns without mixing context.",
  },
  {
    id: "g1",
    cat: "Strategy",
    q: "What kind of customer insights do I get?",
    a: `Once your data is connected, ${BRAND_NAME} helps you see who your best customers are, what they care about, common objections, and where deals tend to stall. Insights stay tied to your workspace so strategy, sales, and marketing work from the same picture.`,
  },
  {
    id: "g2",
    cat: "Strategy",
    q: "What customer data can I connect?",
    a: "Add your company profile, upload documents and spreadsheets, and connect tools like HubSpot, Salesforce, Gong, Intercom, Zendesk, G2/Capterra, Reddit, PostHog, GA4, Notion, Google Drive, Slack, and Jira - with more connectors on the way.",
  },
  {
    id: "m1",
    cat: "Marketing",
    q: "What can I create in the Campaign workspace?",
    a: `Turn your customer and competitive context into launch-ready work: messaging, landing page copy, email drafts, social posts, and a sales battlecard. Your team can review, edit, and reuse assets without starting from a blank page each time.`,
  },
  {
    id: "m2",
    cat: "Marketing",
    q: "Can I generate visual content too?",
    a: `Yes. Content Studio produces on-brand images and short videos from your briefs, aligned with the campaigns you are building in ${BRAND_NAME}.`,
  },
  {
    id: "pr1",
    cat: "Pricing",
    q: "Are the prices on this page final?",
    a: "Yes. The plans and prices shown here are final. Choose monthly or yearly billing on Pro and Team - yearly saves you two months compared to paying month to month.",
  },
  {
    id: "pr2",
    cat: "Pricing",
    q: "Can I start with one workspace and add more later?",
    a: "Yes. Start with a single workspace and add more as you grow - for example, when you take on another client or product line. Each workspace keeps its own data, team access, and campaigns separate.",
  },
  {
    id: "pv1",
    cat: "Privacy",
    q: "Where does my company and customer data live?",
    a: "Inside your secure workspace, available only to you and teammates you invite. Treat it like any sensitive GTM material - profiles, customer notes, and campaign work stay under your account.",
  },
  {
    id: "pv2",
    cat: "Privacy",
    q: "Can one workspace see another workspace's data?",
    a: "No. Workspaces are kept separate. Teammates only see what they are invited to. Joining a new workspace does not remove your access to ones you already belong to.",
  },
];

export const FAQ_CATEGORIES: FaqCategory[] = ["Product", "Strategy", "Marketing", "Pricing", "Privacy"];
