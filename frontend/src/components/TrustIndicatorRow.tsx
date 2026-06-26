import { BookOpen, CheckCircle2, Sparkles } from 'lucide-react'

const trustIndicators = [
  {
    icon: BookOpen,
    title: 'Official Sources',
    description: 'Every answer cites the exact FAR/AIM section.',
    color: 'text-accent',
    bg: 'bg-accent/8',
  },
  {
    icon: CheckCircle2,
    title: 'Verified Excerpts',
    description: 'The quoted source text must match the retrieved chunk.',
    color: 'text-emerald-600',
    bg: 'bg-emerald-50',
  },
  {
    icon: Sparkles,
    title: 'Study Smart',
    description: 'Plain-English answers for student-pilot review.',
    color: 'text-primary',
    bg: 'bg-primary/8',
  },
]

export function TrustIndicatorRow() {
  return (
    <section className="grid gap-5 border-t border-border/60 pt-10 sm:grid-cols-3">
      {trustIndicators.map((indicator) => {
        const Icon = indicator.icon
        return (
          <div
            key={indicator.title}
            className="flex gap-4 rounded-xl border border-border/50 bg-card/60 p-5"
          >
            <div
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${indicator.bg}`}
            >
              <Icon className={`h-5 w-5 ${indicator.color}`} aria-hidden="true" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-foreground">{indicator.title}</h3>
              <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                {indicator.description}
              </p>
            </div>
          </div>
        )
      })}
    </section>
  )
}
