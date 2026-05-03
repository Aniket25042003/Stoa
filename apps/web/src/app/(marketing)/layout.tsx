import { Footer } from "@/components/marketing/Footer";
import { GridBackground } from "@/components/marketing/GridBackground";
import { Navbar } from "@/components/marketing/Navbar";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen">
      <GridBackground />
      <Navbar />
      <main className="relative">{children}</main>
      <Footer />
    </div>
  );
}
