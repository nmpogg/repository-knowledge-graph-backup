import { useRouter } from "vue-router";
import { ORDERS_PATH } from "../router/paths";

export function openOrders() {
  const router = useRouter();
  router.push(ORDERS_PATH);
}

export function openUsers() {
  const router = useRouter();
  router.push({ name: "users" });
}
