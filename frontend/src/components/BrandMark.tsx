import { Sparkles } from 'lucide-react'

export function BrandMark() {
  return (
    <div className="inline-flex items-center gap-3 text-foreground">
      <Sparkles className="h-6 w-6 text-primary" aria-hidden="true" strokeWidth={2.4} />
      <span className="text-xl font-semibold">FARSight</span>
    </div>
  )
}
