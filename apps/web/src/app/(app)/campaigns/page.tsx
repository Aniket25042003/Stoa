import { redirect } from "next/navigation";

export default function CampaignsRedirectPage() {
  redirect("/assets?type=campaigns");
}
