import { createFileRoute } from "@tanstack/react-router";
import { OrderDetailPage } from "./pages";

export const Route = createFileRoute("/orders/$orderId")({
  component: OrderDetailPage,
});
