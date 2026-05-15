import { redirect } from "next/navigation";

type NewRunPageProps = {
  searchParams?: Record<string, string | string[] | undefined>;
};

export default function NewRunPage({ searchParams }: NewRunPageProps) {
  const companyId = searchParams?.company_id;
  const value = Array.isArray(companyId) ? companyId[0] : companyId;
  if (value) {
    redirect(`/gtm?company_id=${encodeURIComponent(value)}`);
  }
  redirect("/gtm");
}
