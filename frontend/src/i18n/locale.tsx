import { Languages } from 'lucide-react'
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { Button } from '../components/ui/Button'
import { en, type MessageKey } from './en'
import { vi } from './vi'

export type Locale = 'en' | 'vi'

const STORAGE_KEY = 'rkg-locale'
const dictionaries: Record<Locale, Record<MessageKey, string>> = { en, vi }

type Params = Record<string, string | number>

export type TranslateFn = (key: MessageKey, params?: Params) => string

interface LocaleApi {
  locale: Locale
  setLocale: (next: Locale) => void
  toggle: () => void
  t: TranslateFn
}

const LocaleContext = createContext<LocaleApi | null>(null)

function readSavedLocale(): Locale {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    return saved === 'vi' ? 'vi' : 'en'
  } catch {
    return 'en'
  }
}

function interpolate(template: string, params?: Params): string {
  if (!params) return template
  return template.replace(/\{(\w+)\}/g, (_, name: string) =>
    params[name] !== undefined ? String(params[name]) : `{${name}}`,
  )
}

export function translate(locale: Locale, key: MessageKey, params?: Params): string {
  const dict = dictionaries[locale] ?? en
  return interpolate(dict[key] ?? en[key] ?? key, params)
}

function applyDocumentLocale(locale: Locale) {
  document.documentElement.lang = locale
  document.title =
    locale === 'vi' ? 'RKG — Đồ thị tri thức kho mã' : 'RKG — Repository knowledge graph'
}

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => readSavedLocale())

  useEffect(() => {
    applyDocumentLocale(locale)
    try {
      localStorage.setItem(STORAGE_KEY, locale)
    } catch {
      /* ignore */
    }
  }, [locale])

  const value = useMemo<LocaleApi>(() => {
    const setLocale = (next: Locale) => setLocaleState(next)
    const toggle = () => setLocaleState((l) => (l === 'en' ? 'vi' : 'en'))
    const t: TranslateFn = (key, params) => translate(locale, key, params)
    return { locale, setLocale, toggle, t }
  }, [locale])

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>
}

export function useLocale(): LocaleApi {
  const ctx = useContext(LocaleContext)
  if (!ctx) throw new Error('useLocale requires LocaleProvider')
  return ctx
}

export function useT(): TranslateFn {
  return useLocale().t
}

export function LocaleToggle() {
  const { locale, toggle, t } = useLocale()
  const nextIsVi = locale === 'en'
  return (
    <Button
      variant="ghost"
      aria-label={nextIsVi ? t('locale.switchToVi') : t('locale.switchToEn')}
      onClick={toggle}
    >
      <Languages size={16} aria-hidden />
      <span>{nextIsVi ? t('locale.vi') : t('locale.en')}</span>
    </Button>
  )
}
