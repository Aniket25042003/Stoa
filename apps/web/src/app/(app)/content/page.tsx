import { redirect } from "next/navigation";

export default function ContentRedirectPage() {
  redirect("/assets?type=content");
}
