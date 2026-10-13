import Router from "vue-router";

const legacyRoutes = [
  {
    path: "/legacy",
    name: "legacy",
    component: () => import("../views/Legacy.vue"),
  },
];

export const legacyRouter = new Router({ routes: legacyRoutes });

export function openLegacy() {
  legacyRouter.replace("/legacy");
}
