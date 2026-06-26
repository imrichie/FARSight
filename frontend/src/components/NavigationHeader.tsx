import { Home } from 'lucide-react'
import { BrandMark } from './BrandMark'

type NavigationHeaderProps = {
  showHomeAction?: boolean
  onHome?: () => void
}

export function NavigationHeader({ showHomeAction = false, onHome }: NavigationHeaderProps) {
  return (
    <header className="sticky top-0 z-10 border-b border-border/60 bg-card/80 backdrop-blur-lg">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3.5">
        <BrandMark onClick={showHomeAction ? onHome : undefined} />
        {showHomeAction ? (
          <button
            type="button"
            onClick={onHome}
            className="inline-flex items-center gap-2 rounded-lg bg-secondary px-3.5 py-2 text-sm font-semibold text-foreground shadow-sm transition-all hover:bg-primary/10 hover:text-primary hover:shadow-md active:scale-[0.97] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
          >
            <Home className="h-4 w-4" aria-hidden="true" />
            New question
          </button>
        ) : null}
      </div>
    </header>
  )
}
