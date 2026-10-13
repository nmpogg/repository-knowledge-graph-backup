import { defineNuxtConfig } from 'nuxt/config'

export const runtimeDefaults = {
  inventoryApiBase: 'https://inventory.example.test',
  inventoryApiKey: '',
  public: {
    apiBase: '/api',
    portalName: 'Order Portal',
  },
}

export default defineNuxtConfig({
  modules: ['@nuxt/eslint'],
  runtimeConfig: runtimeDefaults,
  typescript: {
    strict: true,
    typeCheck: true,
  },
})
