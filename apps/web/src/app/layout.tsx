/**
 * @file apps/web/src/app/layout.tsx
 * @layer Application Source
 * @description Defines shared route layout structure, metadata, and navigation boundaries.
 * @dependencies Next.js, React
 */
import type { Metadata } from "next";
import { Inter, Manrope, Space_Grotesk, Syne, DM_Sans } from "next/font/google";
import Script from "next/script";
import { Analytics } from "@vercel/analytics/next";
import { BRAND_NAME, BRAND_OG_SRC, BRAND_SUBHEAD, BRAND_TAGLINE } from "@/lib/brand";
import { ThemeProvider } from "@/lib/theme";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const manrope = Manrope({ subsets: ["latin"], variable: "--font-manrope", display: "swap" });
const spaceGrotesk = Space_Grotesk({ subsets: ["latin"], variable: "--font-space-grotesk", display: "swap" });
const syne = Syne({ subsets: ["latin"], variable: "--font-syne", display: "swap" });
const dmSans = DM_Sans({ subsets: ["latin"], variable: "--font-dm-sans", display: "swap" });

export const metadata: Metadata = {
  title: {
    default: BRAND_NAME,
    template: `%s | ${BRAND_NAME}`
  },
  description: `${BRAND_TAGLINE} ${BRAND_SUBHEAD}`,
  icons: {
    icon: [{ url: "/images/logos/favicon-32.png", sizes: "32x32", type: "image/png" }],
    apple: [{ url: "/images/logos/stoa-icon-180.png", sizes: "180x180", type: "image/png" }],
  },
  openGraph: {
    title: BRAND_NAME,
    description: `${BRAND_TAGLINE} ${BRAND_SUBHEAD}`,
    url: "https://stoa.ai",
    siteName: BRAND_NAME,
    images: [
      {
        url: BRAND_OG_SRC,
        width: 1200,
        height: 675,
        alt: `${BRAND_NAME} — ${BRAND_TAGLINE}`,
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: BRAND_NAME,
    description: `${BRAND_TAGLINE} ${BRAND_SUBHEAD}`,
    images: [BRAND_OG_SRC],
  },
};

/**
 * Handles root layout behavior for this part of the Stoa application.
 *
 * @param children - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className={`${inter.variable} ${manrope.variable} ${spaceGrotesk.variable} ${syne.variable} ${dmSans.variable}`}>
      <head>
        <Script id="theme-init" strategy="beforeInteractive">
          {`(() => {
            try {
              const saved = localStorage.getItem("gtm-theme");
              const mql = window.matchMedia("(prefers-color-scheme: dark)");
              const wantsDark = saved === "dark" || (saved !== "light" && saved !== "dark" && mql.matches);
              document.documentElement.classList.toggle("dark", wantsDark);
            } catch (_) {}
          })();`}
        </Script>
      </head>
      <body className="min-h-screen font-sans">
        <ThemeProvider>{children}</ThemeProvider>
        <Analytics />
      </body>
    </html>
  );
}
