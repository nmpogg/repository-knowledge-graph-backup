import clsx from 'clsx'
import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  children: ReactNode
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  function Button(
    { variant = 'secondary', className, children, type = 'button', ...rest },
    ref,
  ) {
    return (
      <button
        ref={ref}
        type={type}
        className={clsx('btn', `btn-${variant}`, className)}
        {...rest}
      >
        {children}
      </button>
    )
  },
)
