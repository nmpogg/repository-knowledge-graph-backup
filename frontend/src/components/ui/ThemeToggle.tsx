import { Moon, Sun } from 'lucide-react'
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useT } from '../../i18n'
import { Button } from './Button'

type Theme = 'light' | 'dark'

interface ThemeApi {
  theme: Theme
  toggle: () => void
}

const ThemeContext = createContext<ThemeApi | null>(null)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem('rkg-theme')
    return saved === 'dark' ? 'dark' : 'light'
  })

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('rkg-theme', theme)
  }, [theme])

  const value = useMemo(
    () => ({
      theme,
      toggle: () => setTheme((t) => (t === 'light' ? 'dark' : 'light')),
    }),
    [theme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme(): ThemeApi {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme requires ThemeProvider')
  return ctx
}

export function ThemeToggle() {
  const { theme, toggle } = useTheme()
  const t = useT()
  return (
    <Button
      variant="ghost"
      aria-label={theme === 'light' ? t('theme.toDark') : t('theme.toLight')}
      onClick={toggle}
    >
      {theme === 'light' ? <Moon size={16} aria-hidden /> : <Sun size={16} aria-hidden />}
      <span>{theme === 'light' ? t('theme.dark') : t('theme.light')}</span>
    </Button>
  )
}
