import { redirect } from "next/navigation";
import { getAuthEntryPath } from "@/lib/auth-entry";
import { createClient } from "@/lib/supabase/server";
import { BRAND_NAME } from "@/lib/brand";
import { CompanyOnboardingForm } from "./company-onboarding-form";

export default async function OnboardingPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect(getAuthEntryPath());

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <div className="rounded-[2rem] bg-slate-deep p-7 text-white shadow-card md:p-10">
        <p className="eyebrow text-inverse-primary">Company setup</p>
        <h1 className="mt-4 font-display text-4xl font-extrabold tracking-[-0.045em] md:text-5xl">Tell {BRAND_NAME} about your company.</h1>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-white/68">
          Set up your single company workspace. This becomes the shared context for customer intelligence, competitive monitoring, and campaigns.
        </p>
      </div>
      <div className="rounded-3xl p-6 card-glass md:p-8">
        <CompanyOnboardingForm />
      </div>
    </div>
  );
}
