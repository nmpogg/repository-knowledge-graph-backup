import { useRouter } from "next/navigation";

export default function AccountPage() {
  const router = useRouter();
  router.push("/about");
  return null;
}
