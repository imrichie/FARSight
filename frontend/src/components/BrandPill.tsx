import type { ReactNode } from 'react'

type BrandPillProps = {
  children: ReactNode
  variant?: 'primary' | 'accent' | 'muted'
}

const variantClasses = {
  primary: 'bg-primary/10 text-primary',
  accent: 'bg-accent/5 text-accent',
  muted: 'bg-muted text-muted-foreground',
}

export function BrandPill({ children, variant = 'muted' }: BrandPillProps) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${variantClasses[variant]}`}
    >
      {children}
    </span>
  )
}
