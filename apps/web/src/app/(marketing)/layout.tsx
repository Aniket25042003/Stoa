/**
 * @file apps/web/src/app/(marketing)/layout.tsx
 * @layer Frontend Marketing UI
 * @description Defines shared route layout structure, metadata, and navigation boundaries.
 * @dependencies React
 */
import { Footer } from "@/components/marketing/Footer";
import { Navbar } from "@/components/marketing/Navbar";
import { LenisProvider } from "@/components/marketing/immersive/LenisProvider";

/**
 * Handles marketing layout behavior for this part of the Stoa application.
 *
 * @param children - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <LenisProvider>
      <div className="marketing-v2 relative min-h-screen">
        <Navbar />
        <main className="marketing-v2-scroll relative">{children}</main>
        <Footer />
      </div>
    </LenisProvider>
  );
}
