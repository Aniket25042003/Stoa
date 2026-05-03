import { GridBackground } from "@/components/marketing/GridBackground";

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen">
      <GridBackground />
      {children}
    </div>
  );
}
