import type { ReactNode } from 'react'

type BrandPillProps = {
  children: ReactNode
  variant?: 'primary' | 'accent' | 'muted'
}

const variantClasses = {
  primary: 'bg-gradient-to-r from-primary/15 to-primary/8 text-primary border border-primary/20',
  accent: 'bg-accent/8 text-accent border border-accent/15',
  muted: 'bg-secondary text-muted-foreground border border-border',
}

export function BrandPill({ children, variant = 'muted' }: BrandPillProps) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-xs font-semibold tracking-wide uppercase ${variantClasses[variant]}`}
    >
      {children}
    </span>
  )
}
