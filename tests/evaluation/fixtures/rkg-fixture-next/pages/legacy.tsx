import { redirect } from "next/navigation";
import { ABOUT_PATH } from "../lib/paths";

export default function LegacyPage() {
  redirect(ABOUT_PATH);
  return null;
}
