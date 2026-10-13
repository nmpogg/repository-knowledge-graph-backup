type RuntimeRouter = {
  register: (method: string, path: string, handler: () => unknown) => void
}

export function registerComputedRoute(router: RuntimeRouter, prefix: string) {
  router.register('GET', `${prefix}/runtime`, () => ({ dynamic: true }))
}
