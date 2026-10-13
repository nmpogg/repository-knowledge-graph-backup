import { describe, expect, it } from 'vitest'
import { readResponseMetadata } from './responseMetadata'

describe('persisted response metadata', () => {
  it('keeps unknown legacy and future metadata unknown', () => {
    expect(readResponseMetadata(undefined)).toBeNull()
    expect(readResponseMetadata({ version: 2, coverage: 'complete' })).toBeNull()
    expect(readResponseMetadata({ version: 1, coverage: 'complete' })).toBeNull()
  })
  it('preserves observed limits and language', () => {
    const value = { version: 1, language: 'vi', kind: 'insufficient', subject: null,
      coverage: 'partial', retrieval_truncated: true, history_truncated: false,
      limitations: ['max_nodes'], insufficient_reason: 'entity_not_found' }
    expect(readResponseMetadata(value)).toEqual(value)
  })
})
