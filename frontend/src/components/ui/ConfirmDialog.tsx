import { useEffect, useId, useRef, type ReactNode } from 'react'
import { useT } from '../../i18n'
import { Button } from './Button'

export function ConfirmDialog({
  open,
  title,
  children,
  confirmLabel,
  danger = false,
  onConfirm,
  onCancel,
}: {
  open: boolean
  title: string
  children: ReactNode
  confirmLabel?: string
  danger?: boolean
  onConfirm: () => void
  onCancel: () => void
}) {
  const t = useT()
  const titleId = useId()
  const cancelRef = useRef<HTMLButtonElement>(null)
  const dialogRef = useRef<HTMLDivElement>(null)
  const onCancelRef = useRef(onCancel)
  const resolvedConfirm = confirmLabel ?? t('common.confirm')

  useEffect(() => {
    onCancelRef.current = onCancel
  })

  useEffect(() => {
    if (!open) return
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null
    cancelRef.current?.focus()
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        onCancelRef.current()
        return
      }
      if (event.key !== 'Tab') return
      const node = dialogRef.current
      if (!node) return
      const focusable = Array.from(
        node.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        ),
      ).filter((item) => !item.hasAttribute('disabled'))
      if (focusable.length === 0) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last?.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first?.focus()
      }
    }
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('keydown', onKey)
      previous?.focus()
    }
  }, [open])

  if (!open) return null

  return (
    <div className="dialog-backdrop" role="presentation" onClick={onCancel}>
      <div
        ref={dialogRef}
        className="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id={titleId}>{title}</h2>
        <div>{children}</div>
        <div className="dialog-actions">
          <Button ref={cancelRef} onClick={onCancel}>
            {t('common.cancel')}
          </Button>
          <Button variant={danger ? 'danger' : 'primary'} onClick={onConfirm}>
            {resolvedConfirm}
          </Button>
        </div>
      </div>
    </div>
  )
}
