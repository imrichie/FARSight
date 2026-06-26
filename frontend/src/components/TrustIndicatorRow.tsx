import { BookOpen, CheckCircle2, Sparkles } from 'lucide-react'

const trustIndicators = [
  {
    icon: BookOpen,
    title: 'Official Sources',
    description: 'Every answer cites the exact FAR/AIM section it draws from.',
    gradient: 'from-accent/12 to-accent/5',
    color: 'text-accent',
  },
  {
    icon: CheckCircle2,
    title: 'Verified Excerpts',
    description: 'Quoted text is checked against the retrieved source before it reaches you.',
    gradient: 'from-emerald-100/80 to-emerald-50/50',
    color: 'text-emerald-600',
  },
  {
    icon: Sparkles,
    title: 'Study Smart',
    description: 'Regulation language translated into plain English for student pilots.',
    gradient: 'from-primary/10 to-primary/4',
    color: 'text-primary',
  },
]

export function TrustIndicatorRow() {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      {trustIndicators.map((indicator) => {
        const Icon = indicator.icon
        return (
          <div
            key={indicator.title}
            className={`rounded-2xl bg-gradient-to-br ${indicator.gradient} border border-white/60 p-6`}
            style={{ boxShadow: 'var(--shadow-sm)' }}
          >
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-xl bg-white/70 shadow-sm ${indicator.color}`}
            >
              <Icon className="h-5 w-5" aria-hidden="true" />
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
