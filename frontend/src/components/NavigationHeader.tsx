import { ArrowLeft } from 'lucide-react'
import { BrandMark } from './BrandMark'

type NavigationHeaderProps = {
  showHomeAction?: boolean
  onHome?: () => void
}

export function NavigationHeader({ showHomeAction = false, onHome }: NavigationHeaderProps) {
  return (
    <header className="sticky top-0 z-10 border-b border-border/60 bg-card/80 backdrop-blur-lg">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3.5">
        <BrandMark />
        {showHomeAction ? (
          <button
            type="button"
            onClick={onHome}
            className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Back
          </button>
        ) : null}
      </div>
    </header>
  )
}
