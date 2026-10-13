import clsx from 'clsx'
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Info,
  type LucideIcon,
} from 'lucide-react'
import type { ReactNode } from 'react'

type Tone = 'neutral' | 'success' | 'warning' | 'error' | 'info'

const icons: Record<Tone, LucideIcon | null> = {
  neutral: null,
  success: CheckCircle2,
  warning: AlertTriangle,
  error: AlertCircle,
  info: Info,
}

export function Badge({
  tone = 'neutral',
  children,
}: {
  tone?: Tone
  children: ReactNode
}) {
  const Icon = icons[tone]
  return (
    <span className={clsx('badge', tone !== 'neutral' && `badge-${tone}`)}>
      {Icon ? <Icon size={12} aria-hidden /> : null}
      {children}
    </span>
  )
}
