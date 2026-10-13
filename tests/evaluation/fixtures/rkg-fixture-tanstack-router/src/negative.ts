import { createRoute, useNavigate } from "@tanstack/react-router";
import { CatalogPage, OrdersPage } from "./pages";

export const extraCatalog = createRoute({
  path: "/catalog",
  component: CatalogPage,
});

export function pickParent() {
  return null;
}

export const dangling = createRoute({
  getParentRoute: () => pickParent(),
  path: "dangling",
  component: OrdersPage,
});

export function broken(id: string) {
  const navigate = useNavigate();
  navigate({ to: `/orders/${id}` });
}

function navigate(target: { to: string }) {
  return target.to;
}

export function shadowed() {
  navigate({ to: "/orders" });
}

export function ambiguous() {
  const navigate = useNavigate();
  navigate({ to: "/catalog" });
}
