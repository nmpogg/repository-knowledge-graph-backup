import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'

interface AnnouncerApi {
  announce: (message: string, assertive?: boolean) => void
}

const AnnouncerContext = createContext<AnnouncerApi | null>(null)

export function AnnouncerProvider({ children }: { children: ReactNode }) {
  const [polite, setPolite] = useState('')
  const [assertive, setAssertive] = useState('')

  const announce = useCallback((message: string, isAssertive = false) => {
    if (isAssertive) {
      setAssertive('')
      queueMicrotask(() => setAssertive(message))
    } else {
      setPolite('')
      queueMicrotask(() => setPolite(message))
    }
  }, [])

  const value = useMemo(() => ({ announce }), [announce])

  return (
    <AnnouncerContext.Provider value={value}>
      {children}
      <div className="announcer" aria-live="polite">
        {polite}
      </div>
      <div className="announcer" aria-live="assertive">
        {assertive}
      </div>
    </AnnouncerContext.Provider>
  )
}

export function useAnnouncer(): AnnouncerApi {
  const ctx = useContext(AnnouncerContext)
  if (!ctx) throw new Error('useAnnouncer requires AnnouncerProvider')
  return ctx
}
