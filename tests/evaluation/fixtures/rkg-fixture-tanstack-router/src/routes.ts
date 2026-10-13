import { createRoute } from "@tanstack/react-router";
import { CatalogPage, OrdersPage, RootLayout } from "./pages";
import { ORDERS_SEGMENT } from "./paths";

export const rootRoute = createRoute({
  path: "/",
  component: RootLayout,
});

export const ordersRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: ORDERS_SEGMENT,
  component: OrdersPage,
});

export const catalogRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "catalog",
  component: CatalogPage,
});
