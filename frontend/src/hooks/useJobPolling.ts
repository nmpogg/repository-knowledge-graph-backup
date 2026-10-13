import { useEffect, useState } from 'react'
import { getRkgClient } from '../client'
import type { IndexJob } from '../types/api'

const MAX_BACKOFF = 5

/**
 * Polls an index job, honoring Retry-After (capped), stopping on terminal,
 * and cancelling timers/requests on unmount (AC-RKG-061 M0).
 */
export function useJobPolling(jobId: string | undefined) {
  const [job, setJob] = useState<IndexJob | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(Boolean(jobId))

  useEffect(() => {
    if (!jobId) return

    const client = getRkgClient()
    let cancelled = false
    let timer: ReturnType<typeof setTimeout> | undefined
    let backoff = 1

    const terminal = (stage: string) =>
      ['succeeded', 'succeeded_with_warnings', 'failed'].includes(stage)

    const poll = async () => {
      try {
        const { job: next, retryAfter } = await client.getIndexJob(jobId)
        if (cancelled) return
        setJob(next)
        setError(null)
        setLoading(false)

        if (terminal(next.stage)) return

        const wait = Math.min(retryAfter ?? backoff, MAX_BACKOFF)
        backoff = Math.min(backoff + 1, MAX_BACKOFF)
        timer = setTimeout(poll, wait * 1000)
      } catch (err) {
        if (cancelled) return
        setLoading(false)
        setError(err instanceof Error ? err.message : 'Failed to load job')
        timer = setTimeout(poll, Math.min(backoff, MAX_BACKOFF) * 1000)
        backoff = Math.min(backoff + 1, MAX_BACKOFF)
      }
    }

    void poll()

    return () => {
      cancelled = true
      if (timer) clearTimeout(timer)
    }
  }, [jobId])

  return { job, error, loading, setJob }
}
