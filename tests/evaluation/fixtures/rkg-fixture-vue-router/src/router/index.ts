import { createRouter, createWebHistory } from "vue-router";
import { ORDERS_PATH, USERS_SEGMENT } from "./paths";

const routes = [
  {
    path: "/",
    name: "home",
    component: () => import("../views/Home.vue"),
  },
  {
    path: ORDERS_PATH,
    name: "orders",
    component: () => import("../views/Orders.vue"),
    children: [
      {
        path: ":orderId",
        name: "order-detail",
        component: () => import("../views/OrderDetail.vue"),
      },
    ],
  },
  {
    path: "/admin",
    name: "admin",
    component: () => import("../views/AdminLayout.vue"),
    children: [
      {
        path: USERS_SEGMENT,
        name: "users",
        component: () => import("../views/Users.vue"),
      },
    ],
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
