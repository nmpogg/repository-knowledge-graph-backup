import { translate, type Locale } from '../i18n'

/** Tiny relative-time helper — avoids extra date-fns dependency. */
export function formatDistanceToNow(iso: string, locale: Locale = 'en'): string {
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return iso
  const diff = Math.max(0, Date.now() - then)
  const minutes = Math.floor(diff / 60_000)
  if (minutes < 1) return translate(locale, 'time.justNow')
  if (minutes < 60) return translate(locale, 'time.minutesAgo', { n: minutes })
  const hours = Math.floor(minutes / 60)
  if (hours < 48) return translate(locale, 'time.hoursAgo', { n: hours })
  const days = Math.floor(hours / 24)
  return translate(locale, 'time.daysAgo', { n: days })
}
