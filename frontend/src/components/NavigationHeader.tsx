import { Home } from 'lucide-react'
import { BrandMark } from './BrandMark'

type NavigationHeaderProps = {
  showHomeAction?: boolean
  onHome?: () => void
}

export function NavigationHeader({ showHomeAction = false, onHome }: NavigationHeaderProps) {
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-card/95 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <BrandMark />
        {showHomeAction ? (
          <button
            type="button"
            onClick={onHome}
            className="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
          >
            <Home className="h-4 w-4" aria-hidden="true" />
            Home
          </button>
        ) : null}
      </div>
    </header>
  )
}
