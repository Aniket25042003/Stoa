import { redirect } from "next/navigation";

export default async function NewRunPage({ searchParams }: { searchParams: Promise<{ company_id?: string | string[] | undefined }> }) {
  const sp = await searchParams;
  const raw = sp.company_id;
  const value = Array.isArray(raw) ? raw[0] : raw;
  const cid = typeof value === "string" ? value.trim() : "";
  if (cid) {
    redirect(`/gtm?company_id=${encodeURIComponent(cid)}`);
  }
  redirect("/gtm");
}
