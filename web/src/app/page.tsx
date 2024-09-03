import { fetchSettingsSS } from "@/components/settings/lib";
import { redirect } from "next/navigation";

export default async function Page() {
  const settings = await fetchSettingsSS();

  if (!settings) {
    redirect("/chat");
  }

  if (settings.settings.default_page === "search") {
    redirect("/chat");
  } else {
    redirect("/chat");
  }
}
