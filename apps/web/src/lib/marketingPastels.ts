/** Pastel gradient tokens — each color used at most once per section. */

export const FEATURE_PASTELS = [
  "linear-gradient(135deg, #E8DEFF 0%, #D4E4FF 100%)",
  "linear-gradient(135deg, #FFF4D6 0%, #FFE8A3 100%)",
  "linear-gradient(135deg, #D6F0FF 0%, #B8E8FF 100%)",
  "linear-gradient(135deg, #FFE4EC 0%, #FFC8D8 100%)",
  "linear-gradient(135deg, #FFE4D6 0%, #FFD4C2 100%)",
  "linear-gradient(135deg, #EDE4FF 0%, #D8C8FF 100%)",
] as const;

export const HOW_IT_WORKS_PASTELS = [
  "linear-gradient(135deg, #E8DEFF 0%, #D4E4FF 100%)",
  "linear-gradient(135deg, #D6F0FF 0%, #B8E8FF 100%)",
  "linear-gradient(135deg, #FFF4D6 0%, #FFE8A3 100%)",
  "linear-gradient(135deg, #FFE4D6 0%, #FFD4C2 100%)",
  "linear-gradient(135deg, #FFE4EC 0%, #FFC8D8 100%)",
  "linear-gradient(135deg, #EDE4FF 0%, #D8C8FF 100%)",
] as const;

/** One unique pastel per integration category card. */
export const INTEGRATION_CATEGORY_PASTELS: Record<string, string> = {
  crm: "linear-gradient(135deg, #FFE8D6 0%, #FFCCA8 100%)",
  "sales-intelligence": "linear-gradient(135deg, #E8DEFF 0%, #C8B8FF 100%)",
  support: "linear-gradient(135deg, #D6F0FF 0%, #9ED8FF 100%)",
  reviews: "linear-gradient(135deg, #FFF4D6 0%, #FFE08A 100%)",
  analytics: "linear-gradient(135deg, #FFE4EC 0%, #FFB8D0 100%)",
  knowledge: "linear-gradient(135deg, #EDE4FF 0%, #C8A8FF 100%)",
  "product-feedback": "linear-gradient(135deg, #DFF5E8 0%, #98DDB8 100%)",
  uploads: "linear-gradient(135deg, #F5F0E8 0%, #E0D4C8 100%)",
};

export const CTA_PASTEL = "linear-gradient(135deg, #E0F7E9 0%, #C5EDD4 100%)";
