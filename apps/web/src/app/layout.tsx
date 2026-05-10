import type { Metadata } from "next";
import { Inter, Manrope, Space_Grotesk } from "next/font/google";
import Script from "next/script";
import { ThemeProvider } from "@/lib/theme";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const manrope = Manrope({ subsets: ["latin"], variable: "--font-manrope", display: "swap" });
const spaceGrotesk = Space_Grotesk({ subsets: ["latin"], variable: "--font-space-grotesk", display: "swap" });

export const metadata: Metadata = {
  title: "GTM Agent",
  description: "High-performance multi-agent go-to-market strategy generator",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className={`${inter.variable} ${manrope.variable} ${spaceGrotesk.variable}`}>
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
      </body>
    </html>
  );
}
