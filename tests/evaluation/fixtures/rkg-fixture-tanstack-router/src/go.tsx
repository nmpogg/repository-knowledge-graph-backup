import { Link, useNavigate } from "@tanstack/react-router";
import { ORDERS_PATH } from "./paths";

export function openOrders() {
  const navigate = useNavigate();
  navigate({ to: ORDERS_PATH });
  return <Link to="/orders/$orderId" />;
}
