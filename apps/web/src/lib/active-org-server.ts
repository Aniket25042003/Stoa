import { cookies } from "next/headers";
import { ACTIVE_ORG_COOKIE } from "@/lib/active-org";

export async function getServerActiveOrgId(): Promise<string | null> {
  const jar = await cookies();
  return jar.get(ACTIVE_ORG_COOKIE)?.value ?? null;
}
