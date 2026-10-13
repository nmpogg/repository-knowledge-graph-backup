import { createLiveClient } from './live/liveClient'
import { createMockClient, type RkgClient } from './mock/mockClient'

export type { RkgClient } from './mock/mockClient'

const mode = (import.meta.env.VITE_RKG_CLIENT ?? 'mock') as 'mock' | 'live'

let client: RkgClient | null = null

export function getRkgClient(): RkgClient {
  if (!client) {
    client =
      mode === 'live'
        ? createLiveClient({
            baseUrl: import.meta.env.VITE_RKG_API_BASE ?? '',
            sessionToken: import.meta.env.VITE_RKG_SESSION ?? '',
          })
        : createMockClient()
  }
  return client
}

export function getClientMode(): 'mock' | 'live' {
  return mode === 'live' ? 'live' : 'mock'
}
