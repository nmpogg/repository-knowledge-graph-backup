import { describe, expect, it } from 'vitest'
import { runtimeDefaults } from '../../nuxt.config'

describe('runtime config boundary', () => {
  it('separates private inventory settings from public portal settings', () => {
    expect(runtimeDefaults).toHaveProperty('inventoryApiBase')
    expect(runtimeDefaults).toHaveProperty('inventoryApiKey')
    expect(runtimeDefaults.public).toEqual({ apiBase: '/api', portalName: 'Order Portal' })
    expect(JSON.stringify(runtimeDefaults)).not.toContain('RKG_TEST_SECRET_DO_NOT_PERSIST')
  })
})
