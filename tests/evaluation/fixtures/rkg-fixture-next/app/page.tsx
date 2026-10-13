import Link from "next/link";

const CATALOG_PATH = "/catalog";

export default function HomePage() {
  return (
    <div>
      <Link href="/orders" />
      <Link href={CATALOG_PATH} />
    </div>
  );
}
