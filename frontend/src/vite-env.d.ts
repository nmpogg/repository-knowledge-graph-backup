/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_RKG_CLIENT?: 'mock' | 'live'
  readonly VITE_RKG_API_BASE?: string
  readonly VITE_RKG_SESSION?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
