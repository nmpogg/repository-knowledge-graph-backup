import type { RouteLocationNormalized } from 'vue-router'

export function hasAccountAccess(to: Pick<RouteLocationNormalized, 'meta'>) {
  return to.meta.requiresAccount === true
}

export default defineNuxtRouteMiddleware((to) => {
  if (!hasAccountAccess(to)) {
    return navigateTo('/')
  }
})
