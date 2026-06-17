import { getAuthEntryPath } from "@/lib/auth-entry";

type SignOutRouter = {
  push: (href: string) => void;
  refresh: () => void;
};

export async function signOutClient(router: SignOutRouter): Promise<boolean> {
  try {
    const res = await fetch("/api/auth/signout", { method: "POST" });
    if (!res.ok) {
      console.error("Sign out failed", res.status);
      return false;
    }
    router.push(getAuthEntryPath());
    router.refresh();
    return true;
  } catch (error) {
    console.error("Sign out failed", error);
    return false;
  }
}
