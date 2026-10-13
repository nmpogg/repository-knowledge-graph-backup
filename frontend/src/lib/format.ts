import { formatDistanceToNow } from './time'
import { translate, type Locale } from '../i18n'

export function relativeTime(iso: string, locale: Locale = 'en'): string {
  return formatDistanceToNow(iso, locale)
}

export function shortId(id: string, keep = 10): string {
  if (id.length <= keep) return id
  return `${id.slice(0, keep)}…`
}

export function formatError(err: unknown, locale: Locale = 'en'): string {
  if (err && typeof err === 'object' && 'code' in err && err.code === 'graph_flow_unavailable') {
    return translate(locale, 'error.graph_flow_unavailable')
  }
  if (err && typeof err === 'object' && 'message' in err) {
    return String((err as { message: string }).message)
  }
  return translate(locale, 'error.generic')
}
