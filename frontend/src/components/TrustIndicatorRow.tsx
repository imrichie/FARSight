import { BookOpen, CheckCircle2, Sparkles } from 'lucide-react'

const trustIndicators = [
  {
    icon: BookOpen,
    title: 'Official Sources',
    description: 'Every answer cites the exact FAR/AIM section it draws from.',
    color: 'text-accent',
    bg: 'bg-accent/8',
  },
  {
    icon: CheckCircle2,
    title: 'Verified Excerpts',
    description: 'Quoted text is checked against the retrieved source before it reaches you.',
    color: 'text-emerald-600',
    bg: 'bg-emerald-500/8',
  },
  {
    icon: Sparkles,
    title: 'Study Smart',
    description: 'Regulation language translated into plain English for student pilots.',
    color: 'text-primary',
    bg: 'bg-primary/8',
  },
]

export function TrustIndicatorRow() {
  return (
    <div className="grid gap-6 sm:grid-cols-3">
      {trustIndicators.map((indicator) => {
        const Icon = indicator.icon
        return (
          <div key={indicator.title} className="flex flex-col items-center text-center">
            <div
              className={`flex h-12 w-12 items-center justify-center rounded-2xl ${indicator.bg} ${indicator.color}`}
            >
              <Icon className="h-6 w-6" aria-hidden="true" strokeWidth={1.8} />
            </div>
            <h3 className="mt-4 text-sm font-bold text-foreground">{indicator.title}</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
              {indicator.description}
            </p>
          </div>
        )
      })}
    </div>
  )
}
