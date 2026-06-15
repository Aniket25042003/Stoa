import { Footer } from "@/components/marketing/Footer";
import { Navbar } from "@/components/marketing/Navbar";
import { LenisProvider } from "@/components/marketing/immersive/LenisProvider";

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
